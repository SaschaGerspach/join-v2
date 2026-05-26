import type { CapacitorConfig } from '@capacitor/cli';

const config: CapacitorConfig = {
  appId: 'com.join.app',
  appName: 'Join',
  webDir: 'dist/frontend/browser',
  server: {
    androidScheme: 'https',
  },
  plugins: {
    SplashScreen: {
      launchAutoHide: true,
      backgroundColor: '#2a3647',
    },
    StatusBar: {
      style: 'DARK',
      backgroundColor: '#2a3647',
    },
  },
};

export default config;
