import type { MovieResult } from '../api/searchApi';
import { MovieCard } from './MovieCard';
import '../styles/ResultsGrid.css';

interface ResultsGridProps {
  results: MovieResult[];
  searchType: string;
  isLoading: boolean;
  hasSearched: boolean;
}

export function ResultsGrid({ results, searchType, isLoading, hasSearched }: ResultsGridProps) {
  if (isLoading) {
    return (
      <div className="results-loading">
        <div className="loading-spinner" />
        <p>Searching movies...</p>
      </div>
    );
  }

  if (!hasSearched) {
    return (
      <div className="results-empty">
        <div className="empty-icon">🎬</div>
        <h3>Discover Movies</h3>
        <p>Enter a search query to find movies by mood, theme, or description</p>
      </div>
    );
  }

  if (results.length === 0) {
    return (
      <div className="results-empty">
        <div className="empty-icon">🔍</div>
        <h3>No Results Found</h3>
        <p>Try adjusting your search query or filters</p>
      </div>
    );
  }

  return (
    <div className="results-container">
      <div className="results-header">
        <span className="results-count">{results.length} movies found</span>
        <span className="results-type">Search type: {searchType}</span>
      </div>
      <div className="results-grid">
        {results.map((movie, index) => (
          <MovieCard 
            key={`${movie.title}-${index}`} 
            movie={movie} 
            index={index}
            searchType={searchType}
          />
        ))}
      </div>
    </div>
  );
}

