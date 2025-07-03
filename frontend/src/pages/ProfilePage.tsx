import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { useSelector, useDispatch } from 'react-redux'
import type { AppDispatch, RootState } from '../store/index'
import { fetchUserProfile } from '../store/slices/authSlice'
import LoadingSpinner from '../components/LoadingSpinner'

const ProfilePage = () => {
  const navigate = useNavigate()
  const dispatch = useDispatch<AppDispatch>()
  const { user, isAuthenticated, isLoading } = useSelector((state: RootState) => state.auth)
  const [activeTab, setActiveTab] = useState('profile')

  useEffect(() => {
    if (!isAuthenticated) {
      navigate('/login')
    } else if (!user) {
      dispatch(fetchUserProfile())
    }
  }, [isAuthenticated, user, navigate, dispatch])

  if (isLoading || !user) {
    return <LoadingSpinner />
  }

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <h1 className="text-3xl font-bold mb-8">My Account</h1>

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-8">
        {/* Sidebar */}
        <aside className="lg:col-span-1">
          <nav className="bg-white rounded-lg shadow">
            <ul>
              <li>
                <button
                  onClick={() => setActiveTab('profile')}
                  className={`w-full text-left px-4 py-3 border-b hover:bg-gray-50 ${
                    activeTab === 'profile' ? 'bg-primary-50 text-primary-600 border-l-4 border-primary-600' : ''
                  }`}
                >
                  Profile Information
                </button>
              </li>
              <li>
                <button
                  onClick={() => setActiveTab('orders')}
                  className={`w-full text-left px-4 py-3 border-b hover:bg-gray-50 ${
                    activeTab === 'orders' ? 'bg-primary-50 text-primary-600 border-l-4 border-primary-600' : ''
                  }`}
                >
                  Order History
                </button>
              </li>
              <li>
                <button
                  onClick={() => setActiveTab('addresses')}
                  className={`w-full text-left px-4 py-3 border-b hover:bg-gray-50 ${
                    activeTab === 'addresses' ? 'bg-primary-50 text-primary-600 border-l-4 border-primary-600' : ''
                  }`}
                >
                  Addresses
                </button>
              </li>
              <li>
                <button
                  onClick={() => setActiveTab('password')}
                  className={`w-full text-left px-4 py-3 hover:bg-gray-50 ${
                    activeTab === 'password' ? 'bg-primary-50 text-primary-600 border-l-4 border-primary-600' : ''
                  }`}
                >
                  Change Password
                </button>
              </li>
            </ul>
          </nav>
        </aside>

        {/* Content */}
        <main className="lg:col-span-3">
          <div className="bg-white rounded-lg shadow p-6">
            {activeTab === 'profile' && (
              <div>
                <h2 className="text-xl font-semibold mb-6">Profile Information</h2>
                <form className="space-y-4">
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        First Name
                      </label>
                      <input
                        type="text"
                        value={user.first_name}
                        className="w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                        readOnly
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        Last Name
                      </label>
                      <input
                        type="text"
                        value={user.last_name}
                        className="w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                        readOnly
                      />
                    </div>
                  </div>
                  
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Email Address
                    </label>
                    <input
                      type="email"
                      value={user.email}
                      className="w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                      readOnly
                    />
                  </div>
                  
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Phone Number
                    </label>
                    <input
                      type="tel"
                      value={user.phone || ''}
                      placeholder="Not provided"
                      className="w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                      readOnly
                    />
                  </div>
                  
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Member Since
                    </label>
                    <input
                      type="text"
                      value={new Date(user.created_at).toLocaleDateString()}
                      className="w-full px-4 py-2 border border-gray-300 rounded-md bg-gray-50"
                      readOnly
                    />
                  </div>
                  
                  <div className="flex items-center">
                    <input
                      type="checkbox"
                      checked={user.newsletter_subscription}
                      className="h-4 w-4 text-primary-600 focus:ring-primary-500 border-gray-300 rounded"
                      readOnly
                    />
                    <label className="ml-2 text-sm text-gray-700">
                      Subscribed to newsletter
                    </label>
                  </div>
                  
                  <div className="pt-4">
                    <button
                      type="button"
                      className="bg-primary-600 text-white px-6 py-2 rounded-md font-semibold hover:bg-primary-700 transition-colors"
                      disabled
                    >
                      Edit Profile
                    </button>
                  </div>
                </form>
              </div>
            )}

            {activeTab === 'orders' && (
              <div>
                <h2 className="text-xl font-semibold mb-6">Order History</h2>
                <div className="text-center py-12">
                  <svg className="w-16 h-16 text-gray-400 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
                  </svg>
                  <p className="text-gray-600">No orders yet</p>
                </div>
              </div>
            )}

            {activeTab === 'addresses' && (
              <div>
                <h2 className="text-xl font-semibold mb-6">Saved Addresses</h2>
                <div className="text-center py-12">
                  <svg className="w-16 h-16 text-gray-400 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
                  </svg>
                  <p className="text-gray-600 mb-4">No saved addresses</p>
                  <button className="bg-primary-600 text-white px-4 py-2 rounded-md hover:bg-primary-700 transition-colors">
                    Add New Address
                  </button>
                </div>
              </div>
            )}

            {activeTab === 'password' && (
              <div>
                <h2 className="text-xl font-semibold mb-6">Change Password</h2>
                <form className="space-y-4 max-w-md">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Current Password
                    </label>
                    <input
                      type="password"
                      className="w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                    />
                  </div>
                  
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      New Password
                    </label>
                    <input
                      type="password"
                      className="w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                    />
                  </div>
                  
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Confirm New Password
                    </label>
                    <input
                      type="password"
                      className="w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                    />
                  </div>
                  
                  <div className="pt-4">
                    <button
                      type="submit"
                      className="bg-primary-600 text-white px-6 py-2 rounded-md font-semibold hover:bg-primary-700 transition-colors"
                    >
                      Update Password
                    </button>
                  </div>
                </form>
              </div>
            )}
          </div>
        </main>
      </div>
    </div>
  )
}

export default ProfilePage