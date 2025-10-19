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
        // console.log('Loaded locations:', locs.length, 'metrics:', mets.length);
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
        setClimateData([]);
      } else if (filters.analysisType === 'weighted') {
        const summary = await getClimateSummary(filters);
        // Summary is an object keyed by metric; not directly compatible with ChartContainer’s time-series shape.
        // You can later render this with a dedicated summary component.
        console.log('Summary data:', summary);
        setTrendData(null);
        setClimateData([]);
      } else {
        const cd = await getClimateData(filters);
        setTrendData(null);
        setClimateData(cd);
      }
    } catch (error) {
      console.error('Error fetching data:', error);
    } finally {
      setLoading(false);
    }
  };

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
          <TrendAnalysis 
            data={trendData}
            loading={loading}
          />
        ) : (
          <>
            <ChartContainer 
              title="Climate Trends"
              loading={loading}
              chartType="line"
              data={climateData}
              showQuality={true}
            />
            <ChartContainer 
              title="Quality Distribution"
              loading={loading}
              chartType="bar"
              data={climateData}
              showQuality={true}
            />
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