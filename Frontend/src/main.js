import { createApp } from 'vue'
import App from './App.vue'

import 'vuetify/styles'
import '@mdi/font/css/materialdesignicons.css'

import { createVuetify } from 'vuetify'
import * as components from 'vuetify/components'
import * as directives from 'vuetify/directives'

import './style.css'

const vuetify = createVuetify({
  components,
  directives,
  theme: {
    defaultTheme: 'syntaxLight',
    themes: {
      syntaxLight: {
        dark: false,
        colors: {
          background: '#F5F6FB',
          surface: '#FFFFFF',
          primary: '#1faee9',
          secondary: '#1DB5E8',
          accent: '#6C7AE0',
          error: '#D32F2F',
          info: '#1976D2',
          success: '#2E7D32',
          warning: '#ED6C02'
        }
      }
    }
  }
})

createApp(App)
  .use(vuetify)
  .mount('#app')