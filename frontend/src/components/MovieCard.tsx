import type { MovieResult } from '../api/searchApi';
import '../styles/MovieCard.css';

interface MovieCardProps {
  movie: MovieResult;
  index: number;
  searchType: string;
}

const genreColors: Record<string, string> = {
  action: '#e74c3c',
  comedy: '#f39c12',
  romance: '#e91e63',
  drama: '#9b59b6',
  thriller: '#2c3e50',
  horror: '#1a1a2e',
  scifi: '#00bcd4',
  default: '#7f8c8d',
};

function getGenreColor(genre: string): string {
  return genreColors[genre.toLowerCase()] || genreColors.default;
}

function getScoreDisplay(movie: MovieResult, searchType: string): { label: string; value: string } | null {
  if (searchType === 'vector' || searchType === 'filtered' || searchType === 'range') {
    if (movie.similarity != null) {
      return { label: 'Similarity', value: `${(movie.similarity * 100).toFixed(1)}%` };
    }
  }
  if (searchType === 'keyword' && movie.score != null) {
    return { label: 'BM25 Score', value: movie.score.toFixed(2) };
  }
  // Hybrid scores are shown in the breakdown section
  return null;
}

export function MovieCard({ movie, index, searchType }: MovieCardProps) {
  const genreColor = getGenreColor(movie.genre);
  const scoreDisplay = getScoreDisplay(movie, searchType);

  return (
    <div 
      className="movie-card"
      style={{ 
        animationDelay: `${index * 0.08}s`,
        '--genre-color': genreColor,
      } as React.CSSProperties}
    >
      <div className="movie-poster" style={{ background: `linear-gradient(135deg, ${genreColor}dd, ${genreColor}88)` }}>
        <span className="movie-initial">{movie.title.charAt(0)}</span>
      </div>
      
      <div className="movie-content">
        <div className="movie-header">
          <h3 className="movie-title">{movie.title}</h3>
          <div className="movie-rating">
            <svg viewBox="0 0 24 24" fill="currentColor" className="star-icon">
              <path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z" />
            </svg>
            <span>{movie.rating}</span>
          </div>
        </div>
        
        <span className="movie-genre" style={{ backgroundColor: genreColor }}>
          {movie.genre}
        </span>
        
        <p className="movie-description">{movie.description}</p>
        
        {scoreDisplay && (
          <div className="movie-score">
            <span className="score-label">{scoreDisplay.label}:</span>
            <span className="score-value">{scoreDisplay.value}</span>
          </div>
        )}

        {searchType === 'hybrid' && (
          <div className="hybrid-breakdown">
            <div className="breakdown-item">
              <span>Vector Similarity:</span>
              <span>{movie.vector_similarity?.toFixed(3) ?? 'N/A'}</span>
            </div>
            <div className="breakdown-item">
              <span>Text Score:</span>
              <span>{movie.text_score?.toFixed(2) ?? 'N/A'}</span>
            </div>
            <div className="breakdown-item">
              <span>Hybrid Score:</span>
              <span>{movie.hybrid_score?.toFixed(3) ?? 'N/A'}</span>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
