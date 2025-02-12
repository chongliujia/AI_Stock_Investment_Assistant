import React, { useEffect, useRef } from 'react';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  Title,
  Tooltip,
  Legend,
  Filler,
  ChartType,
  ChartData,
  ChartOptions
} from 'chart.js';
import { Line, Bar } from 'react-chartjs-2';

// 注册 Chart.js 组件
ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  Title,
  Tooltip,
  Legend,
  Filler
);

type ChartComponentType = 'line' | 'bar';

interface Dataset {
  label: string;
  data: number[];
  borderColor?: string;
  backgroundColor?: string;
  fill?: boolean;
  type?: ChartComponentType;
  borderWidth?: number;
  pointRadius?: number;
  tension?: number;
}

interface ChartProps {
  type: ChartComponentType;
  data: {
    labels: string[];
    datasets: Dataset[];
  };
  options?: ChartOptions<ChartComponentType>;
}

const ChartComponent: React.FC<ChartProps> = ({ type, data, options = {} }) => {
  const chartRef = useRef<ChartJS>(null);

  useEffect(() => {
    console.log('ChartComponent mounted with:', { type, data, options });
    return () => {
      if (chartRef.current) {
        chartRef.current.destroy();
      }
    };
  }, []);

  useEffect(() => {
    console.log('ChartComponent data or options updated:', { type, data, options });
  }, [type, data, options]);

  if (!data || !data.labels || !data.datasets) {
    console.warn('ChartComponent: Missing required props:', { data });
    return null;
  }

  const chartData = {
    labels: data.labels,
    datasets: data.datasets.map(dataset => ({
      ...dataset,
      type: dataset.type || type,
      borderWidth: dataset.borderWidth ?? 2,
      pointRadius: dataset.pointRadius ?? 3,
      tension: dataset.tension ?? 0.4
    }))
  };
  
  const chartOptions: ChartOptions<ChartComponentType> = {
    ...options,
    responsive: true,
    maintainAspectRatio: false,
    animation: {
      duration: 750,
      easing: 'easeInOutQuart'
    },
    interaction: {
      mode: 'index',
      intersect: false
    },
    plugins: {
      ...options.plugins,
      tooltip: {
        ...options.plugins?.tooltip,
        enabled: true,
        mode: 'index',
        intersect: false,
        backgroundColor: 'rgba(0, 0, 0, 0.8)',
        titleColor: '#fff',
        bodyColor: '#fff',
        borderColor: 'rgba(255, 255, 255, 0.2)',
        borderWidth: 1
      }
    }
  };

  try {
    return (
      <div style={{ width: '100%', height: '100%', position: 'relative' }}>
        {type === 'line' ? (
          <Line 
            data={chartData as ChartData<'line'>}
            options={chartOptions as ChartOptions<'line'>}
            aria-label="Line chart"
          />
        ) : (
          <Bar
            data={chartData as ChartData<'bar'>}
            options={chartOptions as ChartOptions<'bar'>}
            aria-label="Bar chart"
          />
        )}
      </div>
    );
  } catch (error) {
    console.error('ChartComponent: Error rendering chart:', error);
    throw error; // 让错误边界处理错误
  }
};

export default ChartComponent; 