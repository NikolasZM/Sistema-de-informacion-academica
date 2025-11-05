// src/components/Sidebar.jsx
import {
  FaHome,            // Inicio
  FaUser,            // Personal
  FaChartLine,       // Rendimiento
  FaClipboardList,   // Calificaciones
  FaCalendarCheck,   // Asistencias
  FaBookOpen,       // Libros
  FaFileInvoiceDollar, // Trámites
  FaSignOutAlt       // Cerrar Sesión
} from "react-icons/fa"

export default function Sidebar({ isOpen, onNavigate }) {
  return (
    <aside className={`sidebar ${isOpen ? "open" : ""}`}>
      <nav className="menu">
        <ul>
          <li>
            <a href="#" onClick={() => onNavigate("inicio")}>
              <FaHome /> Inicio
            </a>
          </li>
          <li>
            <a href="#" onClick={() => onNavigate("personal")}>
              <FaUser /> Personal
            </a>
          </li>
          <li>
            <a href="#" onClick={() => onNavigate("rendimiento")}>
              <FaChartLine /> Rendimiento
            </a>
          </li>
          <li>
            <a href="#" onClick={() => onNavigate("cursos")}>
              <FaBookOpen /> Cursos
              </a>
          </li>
          <li>
            <a href="#" onClick={() => onNavigate("calificaciones")}>
              <FaClipboardList /> Calificaciones
            </a>
          </li>
          <li>
            <a href="#" onClick={() => onNavigate("asistencias")}>
              <FaCalendarCheck /> Asistencias
            </a>
          </li>
          <li>
            <a href="#" onClick={() => onNavigate("tramites")}>
              <FaFileInvoiceDollar /> Trámites
            </a>
          </li>
          <li>
              <a href="/logout">
              <FaSignOutAlt /> Cerrar Sesión
            </a>
          </li>
        </ul>
      </nav>
    </aside>
  )
}
