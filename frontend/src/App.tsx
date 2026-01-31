import { useState, useCallback } from 'react';
import { SearchBar } from './components/SearchBar';
import { SearchTypeTabs } from './components/SearchTypeTabs';
import { FilterPanel } from './components/FilterPanel';
import { ResultsGrid } from './components/ResultsGrid';
import { StatusPanel } from './components/StatusPanel';
import { HelpCenter } from './pages/HelpCenter';
import type { SearchType, MovieResult } from './api/searchApi';
import {
  vectorSearch,
  filteredSearch,
  keywordSearch,
  hybridSearch,
  rangeSearch,
} from './api/searchApi';
import './App.css';

type AppPage = 'movies' | 'help';

function App() {
  // Page navigation state
  const [currentPage, setCurrentPage] = useState<AppPage>('movies');

  // Search state
  const [searchType, setSearchType] = useState<SearchType>('vector');
  const [results, setResults] = useState<MovieResult[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [hasSearched, setHasSearched] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [lastQuery, setLastQuery] = useState('');

  // Filter state
  const [genre, setGenre] = useState('all');
  const [minRating, setMinRating] = useState(1);
  const [alpha, setAlpha] = useState(0.5);
  const [distanceThreshold, setDistanceThreshold] = useState(0.5);
  const [numResults, setNumResults] = useState(5);

  const handleSearch = useCallback(async (query: string) => {
    setIsLoading(true);
    setError(null);
    setHasSearched(true);
    setLastQuery(query);

    try {
      let response;

      switch (searchType) {
        case 'vector':
          response = await vectorSearch({ query, num_results: numResults });
          break;
        case 'filtered':
          response = await filteredSearch({
            query,
            num_results: numResults,
            genre: genre !== 'all' ? genre : undefined,
            min_rating: minRating > 1 ? minRating : undefined,
          });
          break;
        case 'keyword':
          response = await keywordSearch({ query, num_results: numResults });
          break;
        case 'hybrid':
          response = await hybridSearch({ query, num_results: numResults, alpha });
          break;
        case 'range':
          response = await rangeSearch({ query, num_results: numResults, distance_threshold: distanceThreshold });
          break;
        default:
          response = await vectorSearch({ query, num_results: numResults });
      }

      setResults(response.results);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred while searching');
      setResults([]);
    } finally {
      setIsLoading(false);
    }
  }, [searchType, genre, minRating, alpha, distanceThreshold, numResults]);

  // Re-run search when search type or filters change (if we have a query)
  const handleSearchTypeChange = useCallback((type: SearchType) => {
    setSearchType(type);
    if (lastQuery && hasSearched) {
      // Delay to allow state update
      setTimeout(() => handleSearch(lastQuery), 0);
    }
  }, [lastQuery, hasSearched, handleSearch]);

  const isHelpPage = currentPage === 'help';
  const isMoviesPage = currentPage === 'movies';

  return (
    <div className="app">
      <nav className="app-nav">
        <button
          className={`nav-btn ${isMoviesPage ? 'active' : ''}`}
          onClick={() => setCurrentPage('movies')}
        >
          Movie Search
        </button>
        <button
          className={`nav-btn ${isHelpPage ? 'active' : ''}`}
          onClick={() => setCurrentPage('help')}
        >
          Help Center
        </button>
      </nav>

      {isHelpPage ? (
        <HelpCenter />
      ) : (
        <>
          <header className="app-header">
            <h1 className="app-title">Movie Recommender</h1>
            <p className="app-subtitle">Discover movies using Redis Vector Search</p>
          </header>

          <main className="app-main">
            <StatusPanel />

            <SearchBar onSearch={handleSearch} isLoading={isLoading} />

            <SearchTypeTabs activeType={searchType} onTypeChange={handleSearchTypeChange} />

            <FilterPanel
              searchType={searchType}
              genre={genre}
              minRating={minRating}
              alpha={alpha}
              distanceThreshold={distanceThreshold}
              numResults={numResults}
              onGenreChange={setGenre}
              onMinRatingChange={setMinRating}
              onAlphaChange={setAlpha}
              onDistanceThresholdChange={setDistanceThreshold}
              onNumResultsChange={setNumResults}
            />

            {error && (
              <div className="error-banner">
                {error}
              </div>
            )}

            <ResultsGrid
              results={results}
              searchType={searchType}
              isLoading={isLoading}
              hasSearched={hasSearched}
            />
          </main>
        </>
      )}
    </div>
  );
}

export default App;
