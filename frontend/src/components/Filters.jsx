import { useMemo } from 'react';
import DatePicker from 'react-datepicker';
import 'react-datepicker/dist/react-datepicker.css';

function Filters({ locations, metrics, filters, onFilterChange, onApplyFilters }) {
  const qualityOptions = ['excellent', 'good', 'questionable', 'poor'];
  const analysisTypes = [
    { key: 'raw', label: 'Raw' },
    { key: 'weighted', label: 'Weighted summary' },
    { key: 'trends', label: 'Trends' },
  ];

  const metricOptions = useMemo(() => {
    return metrics?.map(m => ({
      value: m.name,
      label: m.display_name || m.name,
    })) || [];
  }, [metrics]);

  const toDate = (value) => {
    if (!value) return null;
    const d = new Date(value);
    return isNaN(d.getTime()) ? null : d;
  };

  const toISODate = (date) => {
    if (!date) return '';
    const y = date.getFullYear();
    const m = `${date.getMonth() + 1}`.padStart(2, '0');
    const d = `${date.getDate()}`.padStart(2, '0');
    return `${y}-${m}-${d}`;
  };

  const update = (key, value) => {
    onFilterChange({ ...filters, [key]: value });
  };

  const clearFilters = () => {
    onFilterChange({
      locationId: '',
      startDate: '',
      endDate: '',
      metric: '',
      qualityThreshold: '',
      analysisType: 'raw',
    });
  };

  return (
    <div className="bg-white p-4 rounded-lg shadow-md">
      <h2 className="text-xl font-semibold text-eco-primary mb-4">Filter Data</h2>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {/* Location */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Location</label>
          <select
            className="w-full rounded border-gray-300 focus:border-eco-primary focus:ring-eco-primary"
            value={filters.locationId || ''}
            onChange={(e) => update('locationId', e.target.value)}
          >
            <option value="">All locations</option>
            {locations?.map(loc => (
              <option key={loc.id} value={String(loc.id)}>
                {loc.name}{loc.country ? `, ${loc.country}` : ''}
              </option>
            ))}
          </select>
        </div>

        {/* Metric */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Metric</label>
          <select
            className="w-full rounded border-gray-300 focus:border-eco-primary focus:ring-eco-primary"
            value={filters.metric || ''}
            onChange={(e) => update('metric', e.target.value)}
          >
            <option value="">All metrics</option>
            {metricOptions.map(m => (
              <option key={m.value} value={m.value}>{m.label}</option>
            ))}
          </select>
        </div>

        {/* Quality threshold */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Quality threshold</label>
          <select
            className="w-full rounded border-gray-300 focus:border-eco-primary focus:ring-eco-primary capitalize"
            value={filters.qualityThreshold || ''}
            onChange={(e) => update('qualityThreshold', e.target.value)}
          >
            <option value="">Any quality</option>
            {qualityOptions.map(q => (
              <option key={q} value={q} className="capitalize">{q}</option>
            ))}
          </select>
        </div>

        {/* Start date */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Start date</label>
          <DatePicker
            className="w-full rounded border-gray-300 focus:border-eco-primary focus:ring-eco-primary"
            selected={toDate(filters.startDate)}
            onChange={(d) => update('startDate', toISODate(d))}
            placeholderText="YYYY-MM-DD"
            dateFormat="yyyy-MM-dd"
            isClearable
            maxDate={toDate(filters.endDate) || undefined}
          />
        </div>

        {/* End date */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">End date</label>
          <DatePicker
            className="w-full rounded border-gray-300 focus:border-eco-primary focus:ring-eco-primary"
            selected={toDate(filters.endDate)}
            onChange={(d) => update('endDate', toISODate(d))}
            placeholderText="YYYY-MM-DD"
            dateFormat="yyyy-MM-dd"
            isClearable
            minDate={toDate(filters.startDate) || undefined}
          />
        </div>

        {/* Analysis type */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Analysis type</label>
          <div className="flex gap-2">
            {analysisTypes.map(t => {
              const active = filters.analysisType === t.key;
              return (
                <button
                  key={t.key}
                  type="button"
                  className={`px-3 py-1 rounded border text-sm ${active ? 'bg-eco-primary text-white border-eco-primary' : 'bg-white text-gray-700 border-gray-300 hover:bg-gray-50'}`}
                  onClick={() => update('analysisType', t.key)}
                >
                  {t.label}
                </button>
              );
            })}
          </div>
        </div>
      </div>

      <div className="mt-4 flex flex-wrap gap-2">
        <button
          type="button"
          className="px-4 py-2 rounded bg-eco-primary text-white hover:bg-eco-primary/90"
          onClick={onApplyFilters}
        >
          Apply filters
        </button>
        <button
          type="button"
          className="px-4 py-2 rounded border border-gray-300 text-gray-700 hover:bg-gray-50"
          onClick={clearFilters}
        >
          Clear
        </button>
      </div>
    </div>
  );
}

export default Filters;