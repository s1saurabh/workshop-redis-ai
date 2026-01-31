import type { SearchType } from '../api/searchApi';
import '../styles/SearchTypeTabs.css';

interface SearchTypeTabsProps {
  activeType: SearchType;
  onTypeChange: (type: SearchType) => void;
}

const searchTypes: { type: SearchType; label: string; description: string }[] = [
  { type: 'vector', label: 'Vector', description: 'Semantic similarity search' },
  { type: 'filtered', label: 'Filtered', description: 'Vector + genre/rating filters' },
  { type: 'keyword', label: 'Keyword', description: 'Full-text BM25 search' },
  { type: 'hybrid', label: 'Hybrid', description: 'Vector + keyword combined' },
  { type: 'range', label: 'Range', description: 'Distance threshold filter' },
];

export function SearchTypeTabs({ activeType, onTypeChange }: SearchTypeTabsProps) {
  return (
    <div className="search-type-tabs">
      {searchTypes.map(({ type, label, description }) => (
        <button
          key={type}
          className={`tab-button ${activeType === type ? 'active' : ''}`}
          onClick={() => onTypeChange(type)}
          title={description}
        >
          <span className="tab-label">{label}</span>
          <span className="tab-description">{description}</span>
        </button>
      ))}
    </div>
  );
}

