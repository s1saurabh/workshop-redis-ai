import type { SearchType } from '../api/searchApi';
import '../styles/FilterPanel.css';

interface FilterPanelProps {
  searchType: SearchType;
  genre: string;
  minRating: number;
  alpha: number;
  distanceThreshold: number;
  numResults: number;
  onGenreChange: (genre: string) => void;
  onMinRatingChange: (rating: number) => void;
  onAlphaChange: (alpha: number) => void;
  onDistanceThresholdChange: (threshold: number) => void;
  onNumResultsChange: (num: number) => void;
}

const genres = ['all', 'action', 'comedy', 'romance'];

export function FilterPanel({
  searchType,
  genre,
  minRating,
  alpha,
  distanceThreshold,
  numResults,
  onGenreChange,
  onMinRatingChange,
  onAlphaChange,
  onDistanceThresholdChange,
  onNumResultsChange,
}: FilterPanelProps) {
  const showGenreFilter = searchType === 'filtered';
  const showRatingFilter = searchType === 'filtered';
  const showAlphaSlider = searchType === 'hybrid';
  const showDistanceSlider = searchType === 'range';

  if (!showGenreFilter && !showRatingFilter && !showAlphaSlider && !showDistanceSlider) {
    return null;
  }

  return (
    <div className="filter-panel">
      <div className="filters-row">
        {showGenreFilter && (
          <div className="filter-group">
            <label className="filter-label">Genre</label>
            <select
              className="filter-select"
              value={genre}
              onChange={(e) => onGenreChange(e.target.value)}
            >
              {genres.map((g) => (
                <option key={g} value={g}>
                  {g.charAt(0).toUpperCase() + g.slice(1)}
                </option>
              ))}
            </select>
          </div>
        )}

        {showRatingFilter && (
          <div className="filter-group">
            <label className="filter-label">
              Min Rating: <span className="filter-value">{minRating}</span>
            </label>
            <input
              type="range"
              className="filter-slider"
              min="1"
              max="10"
              value={minRating}
              onChange={(e) => onMinRatingChange(Number(e.target.value))}
            />
          </div>
        )}

        {showAlphaSlider && (
          <div className="filter-group">
            <label className="filter-label">
              Alpha (Vector ↔ Text): <span className="filter-value">{alpha.toFixed(2)}</span>
            </label>
            <div className="slider-labels">
              <span>Vector</span>
              <input
                type="range"
                className="filter-slider alpha-slider"
                min="0"
                max="1"
                step="0.05"
                value={alpha}
                onChange={(e) => onAlphaChange(Number(e.target.value))}
              />
              <span>Text</span>
            </div>
          </div>
        )}

        {showDistanceSlider && (
          <div className="filter-group">
            <label className="filter-label">
              Distance Threshold: <span className="filter-value">{distanceThreshold.toFixed(2)}</span>
            </label>
            <input
              type="range"
              className="filter-slider"
              min="0.1"
              max="1"
              step="0.05"
              value={distanceThreshold}
              onChange={(e) => onDistanceThresholdChange(Number(e.target.value))}
            />
          </div>
        )}

        <div className="filter-group">
          <label className="filter-label">
            Results: <span className="filter-value">{numResults}</span>
          </label>
          <input
            type="range"
            className="filter-slider"
            min="1"
            max="20"
            value={numResults}
            onChange={(e) => onNumResultsChange(Number(e.target.value))}
          />
        </div>
      </div>
    </div>
  );
}

