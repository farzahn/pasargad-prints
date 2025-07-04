import React from 'react';

interface SkeletonLoaderProps {
  type?: 'text' | 'title' | 'image' | 'card' | 'productCard' | 'orderCard' | 'button';
  width?: string;
  height?: string;
  className?: string;
  count?: number;
}

const SkeletonLoader: React.FC<SkeletonLoaderProps> = ({ 
  type = 'text', 
  width = '100%', 
  height, 
  className = '',
  count = 1 
}) => {
  const getHeight = () => {
    if (height) return height;
    switch (type) {
      case 'title': return '2rem';
      case 'text': return '1rem';
      case 'image': return '200px';
      case 'button': return '2.5rem';
      case 'card': return '150px';
      case 'productCard': return '350px';
      case 'orderCard': return '200px';
      default: return '1rem';
    }
  };

  const renderSkeleton = () => {
    const baseClasses = 'animate-pulse bg-gray-200 rounded';
    
    switch (type) {
      case 'productCard':
        return (
          <div className={`bg-white rounded-lg shadow-md overflow-hidden ${className}`}>
            <div className={`${baseClasses} h-64 w-full`} />
            <div className="p-4 space-y-3">
              <div className={`${baseClasses} h-6 w-3/4`} />
              <div className={`${baseClasses} h-4 w-full`} />
              <div className={`${baseClasses} h-4 w-2/3`} />
              <div className="flex justify-between items-center mt-4">
                <div className={`${baseClasses} h-6 w-20`} />
                <div className={`${baseClasses} h-9 w-24`} />
              </div>
            </div>
          </div>
        );
        
      case 'orderCard':
        return (
          <div className={`bg-white rounded-lg shadow p-6 ${className}`}>
            <div className="flex justify-between items-start mb-4">
              <div className="space-y-2 flex-1">
                <div className={`${baseClasses} h-6 w-32`} />
                <div className={`${baseClasses} h-4 w-48`} />
              </div>
              <div className={`${baseClasses} h-8 w-24 rounded-full`} />
            </div>
            <div className="space-y-2">
              <div className={`${baseClasses} h-4 w-full`} />
              <div className={`${baseClasses} h-4 w-3/4`} />
            </div>
            <div className="mt-4 flex justify-between">
              <div className={`${baseClasses} h-5 w-24`} />
              <div className={`${baseClasses} h-5 w-20`} />
            </div>
          </div>
        );
        
      default:
        return (
          <div 
            className={`${baseClasses} ${className}`} 
            style={{ width, height: getHeight() }}
          />
        );
    }
  };

  return (
    <>
      {Array.from({ length: count }).map((_, index) => (
        <React.Fragment key={index}>
          {renderSkeleton()}
        </React.Fragment>
      ))}
    </>
  );
};

export default SkeletonLoader;

// Loading state components for specific use cases
export const ProductGridSkeleton = () => (
  <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
    <SkeletonLoader type="productCard" count={8} />
  </div>
);

export const OrderListSkeleton = () => (
  <div className="space-y-4">
    <SkeletonLoader type="orderCard" count={3} />
  </div>
);

export const ProductDetailSkeleton = () => (
  <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
    <div>
      <SkeletonLoader type="image" height="500px" className="rounded-lg" />
      <div className="mt-4 grid grid-cols-4 gap-2">
        <SkeletonLoader type="image" height="80px" count={4} className="rounded" />
      </div>
    </div>
    <div className="space-y-4">
      <SkeletonLoader type="title" width="75%" />
      <SkeletonLoader type="text" count={3} />
      <SkeletonLoader type="text" width="30%" height="2rem" />
      <SkeletonLoader type="button" width="200px" />
      <div className="pt-6 space-y-2">
        <SkeletonLoader type="text" count={5} />
      </div>
    </div>
  </div>
);

export const CheckoutSkeleton = () => (
  <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
    <div className="bg-white rounded-lg shadow p-6">
      <SkeletonLoader type="title" width="50%" className="mb-4" />
      <div className="space-y-4">
        <SkeletonLoader type="orderCard" />
      </div>
    </div>
    <div className="bg-white rounded-lg shadow p-6 space-y-4">
      <SkeletonLoader type="title" width="60%" />
      <SkeletonLoader type="text" count={4} />
      <SkeletonLoader type="button" />
    </div>
  </div>
);