import { render, screen, fireEvent } from '@testing-library/react';
import { Provider } from 'react-redux';
import { BrowserRouter } from 'react-router-dom';
import { configureStore } from '@reduxjs/toolkit';
import Header from '../Header';
import authReducer from '../../store/slices/authSlice';
import cartReducer from '../../store/slices/cartSlice';

// Mock store setup
const createMockStore = (initialState: Record<string, unknown>) => {
  return configureStore({
    reducer: {
      auth: authReducer,
      cart: cartReducer,
    },
    preloadedState: initialState,
  });
};

const renderWithProviders = (component: React.ReactElement, initialState: Record<string, unknown>) => {
  const store = createMockStore(initialState);
  return render(
    <Provider store={store}>
      <BrowserRouter>
        {component}
      </BrowserRouter>
    </Provider>
  );
};

describe('Header Component', () => {
  const mockAuthenticatedState = {
    auth: {
      isAuthenticated: true,
      user: {
        first_name: 'John',
        last_name: 'Doe',
        email: 'john@example.com',
      },
    },
    cart: {
      cart: {
        total_items: 2,
      },
    },
  };

  test('user dropdown closes when clicking outside', () => {
    renderWithProviders(<Header />, mockAuthenticatedState);
    
    // Find and click the user menu button
    const userMenuButton = screen.getByLabelText('User menu');
    fireEvent.click(userMenuButton);
    
    // Check that dropdown is open
    expect(screen.getByRole('menu')).toBeInTheDocument();
    expect(screen.getByText('Profile')).toBeInTheDocument();
    expect(screen.getByText('Logout')).toBeInTheDocument();
    
    // Click outside the dropdown
    fireEvent.mouseDown(document.body);
    
    // Check that dropdown is closed
    expect(screen.queryByRole('menu')).not.toBeInTheDocument();
  });

  test('user dropdown closes when logout is clicked', () => {
    renderWithProviders(<Header />, mockAuthenticatedState);
    
    // Open dropdown
    const userMenuButton = screen.getByLabelText('User menu');
    fireEvent.click(userMenuButton);
    
    // Click logout
    const logoutButton = screen.getByText('Logout');
    fireEvent.click(logoutButton);
    
    // Check that dropdown is closed
    expect(screen.queryByRole('menu')).not.toBeInTheDocument();
  });

  test('mobile menu and user dropdown use separate state', () => {
    renderWithProviders(<Header />, mockAuthenticatedState);
    
    // Open user dropdown
    const userMenuButton = screen.getByLabelText('User menu');
    fireEvent.click(userMenuButton);
    expect(screen.getByRole('menu')).toBeInTheDocument();
    
    // Open mobile menu - user dropdown should remain open
    const mobileMenuButton = screen.getByLabelText('Mobile menu');
    fireEvent.click(mobileMenuButton);
    
    // Both should be open
    expect(screen.getByRole('menu')).toBeInTheDocument(); // User dropdown
    expect(screen.getByText('Home')).toBeInTheDocument(); // Mobile menu link
  });

  test('ARIA attributes are properly set', () => {
    renderWithProviders(<Header />, mockAuthenticatedState);
    
    const userMenuButton = screen.getByLabelText('User menu');
    
    // Check initial state
    expect(userMenuButton).toHaveAttribute('aria-expanded', 'false');
    expect(userMenuButton).toHaveAttribute('aria-haspopup', 'true');
    
    // Open dropdown
    fireEvent.click(userMenuButton);
    expect(userMenuButton).toHaveAttribute('aria-expanded', 'true');
    
    // Check menu ARIA attributes
    const menu = screen.getByRole('menu');
    expect(menu).toHaveAttribute('aria-orientation', 'vertical');
    
    // Check menu items
    const menuItems = screen.getAllByRole('menuitem');
    expect(menuItems).toHaveLength(2);
  });
});