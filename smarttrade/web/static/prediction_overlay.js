(function(){
  const $ = id => document.getElementById(id);
  let chart, candleSeries, predictedSeries, upperSeries, lowerSeries;
  let smcMarkers = []; // Store SMC markers

  function createChart(){
    const container = $('chart');
    chart = LightweightCharts.createChart(container, {
      layout:{background:{color:'#07102a'},textColor:'#9fb0d9'},
      width: container.clientWidth,
      height: container.clientHeight,
      timeScale:{timeVisible:true,secondsVisible:false}
    });

    candleSeries = chart.addCandlestickSeries({upColor:'#10b981',downColor:'#ef4444',wickUpColor:'#10b981',wickDownColor:'#ef4444'});
    predictedSeries = chart.addLineSeries({color:'#f59e0b',lineWidth:2,title:'Predição'});
    upperSeries = chart.addLineSeries({color:'rgba(245,158,11,0.35)',lineWidth:1,lineStyle:2,title:'Upper'});
    lowerSeries = chart.addLineSeries({color:'rgba(245,158,11,0.35)',lineWidth:1,lineStyle:2,title:'Lower'});

    new ResizeObserver(()=>chart.applyOptions({width:container.clientWidth,height:container.clientHeight})).observe(container);
  }
  
  function drawSMCOverlay(smcData){
    // Clear previous markers
    if(candleSeries && smcMarkers.length > 0){
      candleSeries.setMarkers([]);
      smcMarkers = [];
    }
    
    if(!smcData || !$('show-smc').checked) return;
    
    const markers = [];
    
    // Order Blocks (top 3)
    const obs = smcData.order_blocks || [];
    obs.slice(0,3).forEach((ob,idx)=>{
      const color = ob.type === 'bullish' ? '#10b981' : '#ef4444';
      const shape = ob.type === 'bullish' ? 'arrowUp' : 'arrowDown';
      markers.push({
        time: Math.floor(ob.time/1000),
        position: ob.type === 'bullish' ? 'belowBar' : 'aboveBar',
        color: color,
        shape: shape,
        text: `OB ${ob.type.substring(0,4).toUpperCase()}`
      });
    });
    
    // Fair Value Gaps (top 3)
    const fvgs = smcData.fair_value_gaps || [];
    fvgs.slice(0,3).forEach(fvg=>{
      const color = fvg.type === 'bullish' ? 'rgba(16,185,129,0.6)' : 'rgba(239,68,68,0.6)';
      markers.push({
        time: Math.floor(fvg.time/1000),
        position: fvg.type === 'bullish' ? 'belowBar' : 'aboveBar',
        color: color,
        shape: 'circle',
        text: `FVG`
      });
    });
    
    // Break of Structure
    const bos = smcData.break_of_structure || [];
    bos.slice(-5).forEach(b=>{
      markers.push({
        time: Math.floor(b.time/1000),
        position: b.type === 'bullish' ? 'belowBar' : 'aboveBar',
        color: '#6366f1',
        shape: 'square',
        text: 'BOS'
      });
    });
    
    smcMarkers = markers;
    if(candleSeries){
      candleSeries.setMarkers(markers);
    }
  }

  async function fetchKlines(symbol, interval, limit=500){
    const url = `/api/swap/klines?symbol=${encodeURIComponent(symbol)}&interval=${encodeURIComponent(interval)}&limit=${encodeURIComponent(limit)}`;
    const res = await fetch(url);
    if(!res.ok) throw new Error('Erro ao buscar klines');
    const data = await res.json();
    const klines = data.klines || data;
    return klines.map(c=>({time: Math.floor(c.time/1000), open:+c.open, high:+c.high, low:+c.low, close:+c.close}));
  }

  async function fetchPrediction(symbol, timeframe, periods, model){
    const url = `/api/predict/${encodeURIComponent(symbol)}?timeframe=${encodeURIComponent(timeframe)}&periods=${encodeURIComponent(periods)}&model=${encodeURIComponent(model)}`;
    const res = await fetch(url);
    if(!res.ok) throw new Error('Erro ao pedir predição');
    return await res.json();
  }

  function toLineData(predictions){
    // predictions: array with timestamp(ms) and predicted_price, lower_bound, upper_bound
    const line = predictions.map(p=>({time: Math.floor(p.timestamp/1000), value: +p.predicted_price}));
    const up = predictions.map(p=>({time: Math.floor(p.timestamp/1000), value: +p.upper_bound}));
    const low = predictions.map(p=>({time: Math.floor(p.timestamp/1000), value: +p.lower_bound}));
    return {line, up, low};
  }

  function showSummary(res){
    const summary = $('summary');
    const txt = `${res.symbol} • modelo=${res.model_used} • tendência=${res.trend.toUpperCase()} (${res.trend_strength}%) • confiança média=${(res.predictions.reduce((s,p)=>s+p.confidence,0)/res.predictions.length).toFixed(0)}%`;
    summary.textContent = txt;
  }

  async function fetchPredictionWithSMC(symbol, interval, periods, model){
    const showSMC = $('show-smc').checked;
    if(!showSMC){
      // Use endpoint simples
      return await fetchPrediction(symbol, interval, periods, model);
    }
    
    // Use endpoint com SMC
    const url = `/api/predict/with-smc/${encodeURIComponent(symbol)}?timeframe=${encodeURIComponent(interval)}&periods=${encodeURIComponent(periods)}&model=${encodeURIComponent(model)}`;
    const res = await fetch(url);
    if(!res.ok) throw new Error('Erro ao buscar predição com SMC');
    return await res.json();
  }

  async function refresh(){
    try{
      const symbol = $('symbol').value || 'BTC-USDT';
      const interval = $('interval').value || '1h';
      const periods = parseInt($('periods').value) || 10;
      const model = $('model').value || 'auto';
      const showSMC = $('show-smc').checked;

      $('btn-refresh').disabled = true; $('btn-refresh').textContent = 'Carregando...';

      const klines = await fetchKlines(symbol, interval, 800);
      if(!chart) createChart();
      candleSeries.setData(klines);

      // Ensure visible range to include last candles + predicted horizon
      chart.timeScale().fitContent();

      if(showSMC){
        // Fetch com SMC integrado
        const result = await fetchPredictionWithSMC(symbol, interval, periods, model);
        const pred = result.prediction;
        
        if(pred && pred.predictions && pred.predictions.length){
          const mapped = toLineData(pred.predictions);
          predictedSeries.setData(mapped.line);
          upperSeries.setData(mapped.up);
          lowerSeries.setData(mapped.low);
          showSummary(pred);
          
          // Draw SMC overlay
          drawSMCOverlay(result.smc);
          
          // Show confluence analysis
          if(result.confluence_analysis && result.confluence_analysis.length > 0){
            const confluenceText = result.confluence_analysis.map(c=>`${c.type}: ${c.note}`).join(' | ');
            const summary = $('summary');
            summary.textContent += ` • Confluência: ${result.confluence_analysis.length} sinais`;
            summary.title = confluenceText;
          }
        }
      } else {
        // Fetch sem SMC
        const pred = await fetchPrediction(symbol, interval, periods, model);
        if(pred && pred.predictions && pred.predictions.length){
          const mapped = toLineData(pred.predictions);
          predictedSeries.setData(mapped.line);
          upperSeries.setData(mapped.up);
          lowerSeries.setData(mapped.low);
          showSummary(pred);
        } else {
          predictedSeries.setData([]);
          upperSeries.setData([]);
          lowerSeries.setData([]);
        }
      }

    }catch(e){
      console.error(e);
      alert('Erro: '+(e.message||e));
    }finally{
      $('btn-refresh').disabled = false; $('btn-refresh').textContent = 'Atualizar';
    }
  }

  window.addEventListener('DOMContentLoaded', ()=>{
    // Init elements
    $('btn-refresh').addEventListener('click', refresh);
    $('show-smc').addEventListener('change', refresh);
    // Try to detect if prophet is available and enable model option
    fetch('/api/predict/BTC-USDT?timeframe=1h&periods=1&model=auto',{method:'GET'}).then(()=>{/*ok*/}).catch(()=>{/*ignore*/});
    // Create chart placeholder
    createChart();
    // Initial load
    refresh();
  });
})();
