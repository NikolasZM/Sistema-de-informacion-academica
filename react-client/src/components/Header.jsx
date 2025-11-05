// Requiere instalar react-icons: npm i react-icons
import { FaBars } from "react-icons/fa"
import logoCetpro from "../assets/logotipo-ceptro.png"

export default function Header({ toggleSidebar, sidebarOpen }) {
  return (
    // Barra superior (sticky en CSS). Ocupa todo el ancho.
    <header className="topbar">
      {/* Lado izquierdo: botón hamburguesa + título "ESTUDIANTE" */}
      <div className="left">
        {/* El botón tiene clase "active" cuando el sidebar está abierto
            para dar feedback visual (color/fondo). */}
        <button
          className={`hamburger ${sidebarOpen ? "active" : ""}`}
          onClick={toggleSidebar}
          aria-label="Abrir/Cerrar menú"
        >
          <FaBars />
        </button>

        <span className="brand-title">ESTUDIANTE</span>
      </div>

      {/* Derecha: LOGO CETPRO (reemplaza caja del usuario) */}
      <div className="userbox">
        <img
          src={logoCetpro}
          alt="CETPRO"
          className="logo-cetpro"
          draggable="false"
        />
      </div>

      {/* Lado derecho: información del usuario */}
      {/*<div className="userbox">*/}
        {/*<img className="avatar" src="https://i.pravatar.cc/48?img=12" alt="Foto de perfil" />*/}
        {/*<div className="meta">*/}
          {/*<div className="name">Nombre del estudiante</div> */}
          {/*<div className="role">Carrera</div> */}
          {/*<div className="name">{user?.nombre_completo || "Estudiante"}</div> */}
        {/*</div>*/}
      {/*</div>*/}
    </header>
  )
}
