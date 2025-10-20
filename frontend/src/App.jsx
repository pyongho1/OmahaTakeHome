import { useState, useEffect } from 'react';
import Filters from './components/Filters';
import ChartContainer from './components/ChartContainer';
import TrendAnalysis from './components/TrendAnalysis';
import QualityIndicator from './components/QualityIndicator';
import { getLocations, getMetrics, getClimateData, getClimateSummary, getTrends } from './api';

function App() {
  const [locations, setLocations] = useState([]);
  const [metrics, setMetrics] = useState([]);
  const [climateData, setClimateData] = useState([]);
  const [trendData, setTrendData] = useState(null);
  const [summary, setSummary] = useState(null);
  const [filters, setFilters] = useState({
    locationId: '',
    startDate: '',
    endDate: '',
    metric: '',
    qualityThreshold: '',
    analysisType: 'raw'
  });
  const [loading, setLoading] = useState(false);

  // Existing useEffect for locations and metrics
  useEffect(() => {
    let active = true;
    (async () => {
      try {
        const [locs, mets] = await Promise.all([getLocations(), getMetrics()]);
        if (!active) return;
        setLocations(locs);
        setMetrics(mets);
        console.log('Loaded locations:', locs.length, 'metrics:', mets.length);
      } catch (e) {
        console.error('Failed to load reference data', e);
      }
    })();
    return () => { active = false; };
  }, []);

  // Updated fetch function to handle different analysis types
  const fetchData = async () => {
    setLoading(true);
    try {
      if (filters.analysisType === 'trends') {
        const td = await getTrends(filters);
        setTrendData(td);
        setSummary(null);
        setClimateData([]);
      } else if (filters.analysisType === 'weighted') {
        const s = await getClimateSummary(filters);
        setSummary(s);
        setTrendData(null);
        setClimateData([]);
      } else {
        const cd = await getClimateData(filters);
        setTrendData(null);
        setSummary(null);
        setClimateData(cd);
      }
    } catch (error) {
      console.error('Error fetching data:', error);
    } finally {
      setLoading(false);
    }
  };
  
  const pct = (x) => (x == null ? '-' : `${(x * 100).toFixed(1)}%`);

  return (
    <div className="container mx-auto px-4 py-8 max-w-6xl">
      <header className="mb-8 text-center">
        <h1 className="text-4xl font-bold text-eco-primary mb-2">
          EcoVision: Climate Visualizer
        </h1>
        <p className="text-gray-600 italic">
          Transforming climate data into actionable insights for a sustainable future
        </p>
      </header>

      <Filters 
        locations={locations}
        metrics={metrics}
        filters={filters}
        onFilterChange={setFilters}
        onApplyFilters={fetchData}
      />

<div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mt-8">
  {filters.analysisType === 'trends' ? (
    <TrendAnalysis data={trendData} loading={loading} />
  ) : filters.analysisType === 'weighted' ? (
    <div className="col-span-2">
      <h2 className="text-xl font-semibold mb-4">Weighted Summary</h2>
      {loading ? (
        <div className="text-gray-500">Loading summary…</div>
      ) : !summary || Object.keys(summary).length === 0 ? (
        <div className="text-gray-500">No summary data.</div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {Object.entries(summary).map(([metric, info]) => (
            <div key={metric} className="rounded border p-4">
              <div className="flex items-baseline justify-between mb-2">
                <h3 className="text-lg font-semibold capitalize">{metric}</h3>
                <span className="text-sm text-gray-500">{info.unit}</span>
              </div>
              <div className="grid grid-cols-3 gap-2 text-sm mb-3">
                <div><div className="text-gray-500">Min</div><div className="font-medium">{info.min?.toFixed?.(1) ?? info.min}</div></div>
                <div><div className="text-gray-500">Avg</div><div className="font-medium">{info.avg?.toFixed?.(1) ?? info.avg}</div></div>
                <div><div className="text-gray-500">Max</div><div className="font-medium">{info.max?.toFixed?.(1) ?? info.max}</div></div>
              </div>
              {'weighted_avg' in info && (
                <div className="text-sm mb-3">
                  <div className="text-gray-500">Weighted Avg</div>
                  <div className="font-medium">{info.weighted_avg?.toFixed?.(1) ?? info.weighted_avg} {info.unit}</div>
                </div>
              )}
              {info.quality_distribution && (
                <div className="text-sm">
                  <div className="text-gray-500 mb-1">Quality Distribution</div>
                  <div className="grid grid-cols-4 gap-2">
                    <div><div className="text-gray-500">Excellent</div><div className="font-medium">{pct(info.quality_distribution.excellent)}</div></div>
                    <div><div className="text-gray-500">Good</div><div className="font-medium">{pct(info.quality_distribution.good)}</div></div>
                    <div><div className="text-gray-500">Questionable</div><div className="font-medium">{pct(info.quality_distribution.questionable)}</div></div>
                    <div><div className="text-gray-500">Poor</div><div className="font-medium">{pct(info.quality_distribution.poor)}</div></div>
                  </div>
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  ) : (
    <>
      <ChartContainer title="Climate Trends" loading={loading} chartType="line" data={climateData} showQuality={true} />
      <ChartContainer title="Quality Distribution" loading={loading} chartType="bar" data={climateData} showQuality={true} />
    </>
  )}
</div>

      <QualityIndicator 
        data={climateData}
        className="mt-6"
      />
    </div>
  );
}

export default App;