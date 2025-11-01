(function(){
  const $ = id => document.getElementById(id);
  let chart, candleSeries, predictedSeries, upperSeries, lowerSeries;

  function createChart(){
    const container = $('chart');
    chart = LightweightCharts.createChart(container, {
      layout:{background:{color:'#07102a'},textColor:'#9fb0d9'},
      width: container.clientWidth,
      height: container.clientHeight,
      timeScale:{timeVisible:true,secondsVisible:false}
    });

    candleSeries = chart.addCandlestickSeries({upColor:'#10b981',downColor:'#ef4444',wickUpColor:'#10b981',wickDownColor:'#ef4444'});
    predictedSeries = chart.addLineSeries({color:'#f59e0b',lineWidth:2});
    upperSeries = chart.addLineSeries({color:'rgba(245,158,11,0.35)',lineWidth:1,lineStyle:2});
    lowerSeries = chart.addLineSeries({color:'rgba(245,158,11,0.35)',lineWidth:1,lineStyle:2});

    new ResizeObserver(()=>chart.applyOptions({width:container.clientWidth,height:container.clientHeight})).observe(container);
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

  async function refresh(){
    try{
      const symbol = $('symbol').value || 'BTC-USDT';
      const interval = $('interval').value || '1h';
      const periods = parseInt($('periods').value) || 10;
      const model = $('model').value || 'auto';

      $('btn-refresh').disabled = true; $('btn-refresh').textContent = 'Carregando...';

      const klines = await fetchKlines(symbol, interval, 800);
      if(!chart) createChart();
      candleSeries.setData(klines);

      // Ensure visible range to include last candles + predicted horizon
      chart.timeScale().fitContent();

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
    // Try to detect if prophet is available and enable model option
    fetch('/api/predict/BTC-USDT?timeframe=1h&periods=1&model=auto',{method:'GET'}).then(()=>{/*ok*/}).catch(()=>{/*ignore*/});
    // Create chart placeholder
    createChart();
    // Initial load
    refresh();
  });
})();
