import { useEffect, useState } from 'react';
import { useLocation } from 'react-router-dom';

interface GlobalLoadingOverlayProps {
  isLoading?: boolean;
  message?: string;
}

const GlobalLoadingOverlay: React.FC<GlobalLoadingOverlayProps> = ({ 
  isLoading = false, 
  message = 'Loading...' 
}) => {
  const [show, setShow] = useState(false);
  const location = useLocation();

  useEffect(() => {
    // Reset loading state on route change
    setShow(false);
  }, [location]);

  useEffect(() => {
    if (isLoading) {
      // Delay showing the overlay to prevent flash for quick operations
      const timer = setTimeout(() => setShow(true), 100);
      return () => clearTimeout(timer);
    } else {
      setShow(false);
    }
  }, [isLoading]);

  if (!show) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      {/* Backdrop */}
      <div className="absolute inset-0 bg-black bg-opacity-50 backdrop-blur-sm" />
      
      {/* Loading content */}
      <div className="relative bg-white rounded-lg shadow-xl p-8 max-w-sm w-full mx-4">
        <div className="flex flex-col items-center">
          {/* Spinner */}
          <div className="relative">
            <div className="w-16 h-16 border-4 border-gray-200 rounded-full"></div>
            <div className="absolute top-0 left-0 w-16 h-16 border-4 border-primary-600 rounded-full animate-spin border-t-transparent"></div>
          </div>
          
          {/* Message */}
          <p className="mt-4 text-gray-700 font-medium">{message}</p>
          
          {/* Progress dots */}
          <div className="flex gap-1 mt-4">
            <div className="w-2 h-2 bg-primary-600 rounded-full animate-bounce" style={{ animationDelay: '0ms' }}></div>
            <div className="w-2 h-2 bg-primary-600 rounded-full animate-bounce" style={{ animationDelay: '150ms' }}></div>
            <div className="w-2 h-2 bg-primary-600 rounded-full animate-bounce" style={{ animationDelay: '300ms' }}></div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default GlobalLoadingOverlay;