import { ref } from 'vue'

const STORAGE_KEY = 'autogate-server-theme'

// module-level singleton — semua komponen yang import ini share state yang sama
const theme = ref(localStorage.getItem(STORAGE_KEY) || 'dark')

function applyTheme(value) {
  if (value === 'light') {
    document.documentElement.classList.add('light')
  } else {
    document.documentElement.classList.remove('light')
  }
}

// apply saat pertama kali file ini di-import
applyTheme(theme.value)

function toggleTheme() {
  theme.value = theme.value === 'dark' ? 'light' : 'dark'
  localStorage.setItem(STORAGE_KEY, theme.value)
  applyTheme(theme.value)
}

export function useTheme() {
  return { theme, toggleTheme }
}
