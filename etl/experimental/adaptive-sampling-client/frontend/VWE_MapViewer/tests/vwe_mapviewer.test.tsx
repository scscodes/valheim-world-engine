import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { jest } from '@jest/globals';
import VWE_MapViewer from '@/components/VWE_MapViewer';

// Mock the custom hook
jest.mock('@/hooks/useVWE_MapViewer', () => ({
  useVWE_MapViewer: jest.fn(),
}));

const mockUseVWE_MapViewer = require('@/hooks/useVWE_MapViewer').useVWE_MapViewer;

describe('VWE_MapViewer Component', () => {
  const mockData = {
    id: '1',
    name: 'Test VWE_MapViewer',
    description: 'Test description',
    status: 'completed',
    createdAt: '2023-01-01T00:00:00Z',
    updatedAt: '2023-01-01T00:00:00Z',
  };

  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('renders loading state', () => {
    mockUseVWE_MapViewer.mockReturnValue({
      data: null,
      loading: true,
      error: null,
      refetch: jest.fn(),
      create: jest.fn(),
      update: jest.fn(),
      remove: jest.fn(),
    });

    render(<VWE_MapViewer />);
    
    expect(screen.getByText('Loading...')).toBeInTheDocument();
  });

  it('renders error state', () => {
    const mockRefetch = jest.fn();
    mockUseVWE_MapViewer.mockReturnValue({
      data: null,
      loading: false,
      error: 'Test error',
      refetch: mockRefetch,
      create: jest.fn(),
      update: jest.fn(),
      remove: jest.fn(),
    });

    render(<VWE_MapViewer />);
    
    expect(screen.getByText('Error loading data')).toBeInTheDocument();
    expect(screen.getByText('Test error')).toBeInTheDocument();
    
    const retryButton = screen.getByText('Try again');
    fireEvent.click(retryButton);
    expect(mockRefetch).toHaveBeenCalled();
  });

  it('renders component with data', () => {
    mockUseVWE_MapViewer.mockReturnValue({
      data: mockData,
      loading: false,
      error: null,
      refetch: jest.fn(),
      create: jest.fn(),
      update: jest.fn(),
      remove: jest.fn(),
    });

    render(<VWE_MapViewer />);
    
    expect(screen.getByText('VWE_MapViewer Component')).toBeInTheDocument();
    expect(screen.getByText('Counter Example')).toBeInTheDocument();
    expect(screen.getByText('API Data')).toBeInTheDocument();
  });

  it('handles counter increment', () => {
    mockUseVWE_MapViewer.mockReturnValue({
      data: mockData,
      loading: false,
      error: null,
      refetch: jest.fn(),
      create: jest.fn(),
      update: jest.fn(),
      remove: jest.fn(),
    });

    render(<VWE_MapViewer />);
    
    const incrementButton = screen.getByText('+');
    const countDisplay = screen.getByText('0');
    
    fireEvent.click(incrementButton);
    expect(countDisplay).toHaveTextContent('1');
    
    fireEvent.click(incrementButton);
    expect(countDisplay).toHaveTextContent('2');
  });

  it('handles counter decrement', () => {
    mockUseVWE_MapViewer.mockReturnValue({
      data: mockData,
      loading: false,
      error: null,
      refetch: jest.fn(),
      create: jest.fn(),
      update: jest.fn(),
      remove: jest.fn(),
    });

    render(<VWE_MapViewer />);
    
    const incrementButton = screen.getByText('+');
    const decrementButton = screen.getByText('-');
    const countDisplay = screen.getByText('0');
    
    // Increment first
    fireEvent.click(incrementButton);
    expect(countDisplay).toHaveTextContent('1');
    
    // Then decrement
    fireEvent.click(decrementButton);
    expect(countDisplay).toHaveTextContent('0');
    
    // Decrement should not go below 0
    fireEvent.click(decrementButton);
    expect(countDisplay).toHaveTextContent('0');
  });

  it('displays API data when available', () => {
    mockUseVWE_MapViewer.mockReturnValue({
      data: mockData,
      loading: false,
      error: null,
      refetch: jest.fn(),
      create: jest.fn(),
      update: jest.fn(),
      remove: jest.fn(),
    });

    render(<VWE_MapViewer />);
    
    expect(screen.getByText('API Data')).toBeInTheDocument();
    expect(screen.getByText(JSON.stringify(mockData, null, 2))).toBeInTheDocument();
  });
});
