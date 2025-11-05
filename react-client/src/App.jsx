import { useEffect, useState } from "react"

// Tus componentes
import Sidebar from "./components/Sidebar.jsx"
import Header from "./components/Header.jsx"
import Grades from "./pages/Grades.jsx"
import Attendance from "./pages/Attendance.jsx"
import Courses from "./pages/Courses.jsx"
import Tramites from "./pages/Tramites.jsx"
import Personal from "./pages/Personal.jsx"
import Rendimiento from "./pages/Rendimiento.jsx"
import Inicio       from "./pages/Inicio.jsx"
import DashboardStats from "./components/DashboardStats.jsx"

export default function App() {
  // Estado de layout
  const [sidebarOpen, setSidebarOpen] = useState(true)
  const [isMobile, setIsMobile] = useState(false)
  const [page, setPage] = useState("inicio")

  // 🔹 Nuevo: estado de usuario autenticado
  const [user, setUser] = useState(null)
  const [loading, setLoading] = useState(true)

  // 🔹 Verificar sesión apenas carga React
  useEffect(() => {
      fetch("/api/estudiante/info", {
        method: "GET",
        credentials: "include", // 🔥 OBLIGATORIO
      })
      .then(res => {
        if (res.status === 401) {
          window.location.href = "/login"
          return null
        }
        return res.json()
      })
      .then(data => {
        if (data) setUser(data)
        setLoading(false)
      })
      .catch(err => {
        console.error("Error:", err)
        setLoading(false)
      })
  }, [])

  // Layout responsivo
  useEffect(() => {
    const checkScreen = () => {
      const mobile = window.matchMedia("(max-width: 768px)").matches
      setIsMobile(mobile)
      setSidebarOpen(!mobile)
    }
    checkScreen()
    window.addEventListener("resize", checkScreen)
    return () => window.removeEventListener("resize", checkScreen)
  }, [])

  const handleNavigate = (newPage) => {
    setPage(newPage)
    if (isMobile) setSidebarOpen(false)
  }

  // 🔹 Mientras carga o no hay sesión
  if (loading) return <p>Cargando...</p>
  if (!user) return null // React redirige automáticamente al login

  return (
    <div className="layout">
      <Header toggleSidebar={() => setSidebarOpen(prev => !prev)} sidebarOpen={sidebarOpen} />
      <div className="body">
        <Sidebar isOpen={sidebarOpen} onNavigate={handleNavigate} />
        <main className="page">
           {page === "dashboard" && (
            <>
              <h1>Bienvenido, {user.nombre_completo}</h1>
              {/*<DashboardStats estId={user.id} />*/}
              <p>Programa: {user.programa_estudio}</p>
              <p>DNI: {user.dni}</p>
              <p>DNI: {user.dni}</p>
              <p>Sexo: {user.sexo}</p>
              <p>Código: {user.codigo}</p>
              <p>Selecciona una opción en el menú lateral.</p>
            </>
          )}
          {page === "inicio"      && <Inicio user={user} />} 
          {page === "calificaciones" && <Grades />}
          {page === "asistencias" && <Attendance />}
          {page === "cursos" && <Courses />}
          {page === "tramites" && <Tramites />}
          {page === "personal" && <Personal />}
          {page === "rendimiento" && <Rendimiento />}
        </main>
      </div>
      {sidebarOpen && isMobile && (
        <div className="overlay" onClick={() => setSidebarOpen(false)} />
      )}
    </div>
  )
}
