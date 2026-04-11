import { AuthProvider } from './context/AuthContext'
import AppRouter from './router/index'
import './styles/tokens.css'
import './styles/global.css'
import './styles/shell.css'

export default function App() {
  return (
    <AuthProvider>
      <AppRouter />
    </AuthProvider>
  )
}
