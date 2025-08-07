// Configuration file for environment variables
const config = {
  // Backend URL - this will be replaced during build time
  BACKEND_URL: import.meta.env.VITE_BACKEND_URL || 'http://localhost:8000',
  
  // Development mode
  IS_DEV: import.meta.env.DEV,
  
  // Production mode
  IS_PROD: import.meta.env.PROD,
  
  // Get the current environment
  getEnvironment() {
    if (this.IS_DEV) return 'development';
    if (this.IS_PROD) return 'production';
    return 'unknown';
  },
  
  // Check if backend URL is properly configured
  isBackendConfigured() {
    return this.BACKEND_URL && this.BACKEND_URL !== 'http://localhost:8000';
  },
  
  // Get backend URL with fallback
  getBackendUrl() {
    if (!this.isBackendConfigured()) {
      console.warn('⚠️ VITE_BACKEND_URL not configured. Using localhost fallback.');
      console.warn('⚠️ Please set VITE_BACKEND_URL environment variable in your deployment platform.');
    }
    return this.BACKEND_URL;
  }
};

export default config; 