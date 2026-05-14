import React, { useContext, useState } from 'react';
import { NavLink, Outlet, useNavigate, useLocation } from 'react-router-dom';
import { AuthContext } from '../context/AuthContext';
import { User, DollarSign, Receipt, MessageSquare, Bell, Utensils, LogOut, Menu, X } from 'lucide-react';

const StudentLayout = () => {
    const { user, logout } = useContext(AuthContext);
    const [sidebarOpen, setSidebarOpen] = useState(false);
    const location = useLocation();

    const getPageTitle = () => {
        switch (location.pathname) {
            case '/': return 'My Profile';
            case '/fees': return 'Fee Status';
            case '/receipts': return 'My Receipts';
            case '/complaints': return 'Complaints';
            case '/notices': return 'Notices';
            case '/food': return 'Food & Meals';
            default: return 'Student Dashboard';
        }
    };

    const navLinks = [
        { path: '/', label: 'My Profile', icon: User },
        { path: '/fees', label: 'Fee Status', icon: DollarSign },
        { path: '/receipts', label: 'My Receipts', icon: Receipt },
        { path: '/complaints', label: 'Complaints', icon: MessageSquare },
        { path: '/notices', label: 'Notices', icon: Bell },
        { path: '/food', label: 'Food & Meals', icon: Utensils },
    ];

    return (
        <div className="flex h-screen bg-gray-50 font-sans">
            {/* Mobile Sidebar Overlay */}
            {sidebarOpen && (
                <div 
                    className="fixed inset-0 bg-black/50 z-40 md:hidden"
                    onClick={() => setSidebarOpen(false)}
                />
            )}

            {/* Sidebar */}
            <aside className={`
                fixed inset-y-0 left-0 z-50 w-64 bg-[#1e2b3c] text-white flex flex-col
                transition-transform duration-300 ease-in-out md:translate-x-0 md:static
                ${sidebarOpen ? 'translate-x-0' : '-translate-x-full'}
            `}>
                <div className="p-4 border-b border-gray-700/50 flex items-center justify-between">
                    <div>
                        <h2 className="text-xl font-bold flex items-center gap-2">
                            <span className="text-orange-400">⛺</span> CBH
                        </h2>
                        <div className="text-xs text-gray-400 mt-1">Student Portal</div>
                    </div>
                    <button className="md:hidden" onClick={() => setSidebarOpen(false)}>
                        <X size={20} className="text-gray-400" />
                    </button>
                </div>

                <div className="p-6 border-b border-gray-700/50 flex items-center gap-3">
                    <div className="w-10 h-10 rounded-full bg-orange-500 flex items-center justify-center font-bold text-lg">
                        {user?.name?.charAt(0)?.toUpperCase()}
                    </div>
                    <div className="overflow-hidden">
                        <div className="font-bold truncate">{user?.name}</div>
                        <div className="text-xs text-gray-400">STUDENT</div>
                    </div>
                </div>

                <div className="p-4 text-xs font-bold text-gray-500">MENU</div>
                
                <nav className="flex-1 overflow-y-auto">
                    <ul className="space-y-1 px-3">
                        {navLinks.map((link) => (
                            <li key={link.path}>
                                <NavLink
                                    to={link.path}
                                    onClick={() => setSidebarOpen(false)}
                                    className={({ isActive }) => `
                                        flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm transition-colors
                                        ${isActive 
                                            ? 'bg-white/10 text-white font-semibold border-l-4 border-orange-500' 
                                            : 'text-gray-300 hover:bg-white/5 hover:text-white'}
                                    `}
                                >
                                    <link.icon size={18} className={location.pathname === link.path ? 'text-orange-400' : 'text-gray-400'} />
                                    {link.label}
                                </NavLink>
                            </li>
                        ))}
                    </ul>
                </nav>

                <div className="p-4 border-t border-gray-700/50">
                    <button 
                        onClick={logout}
                        className="flex items-center gap-3 px-3 py-2 text-sm text-gray-300 hover:text-white w-full transition-colors"
                    >
                        <LogOut size={18} /> Logout
                    </button>
                </div>
            </aside>

            {/* Main Content Area */}
            <main className="flex-1 flex flex-col h-screen overflow-hidden">
                {/* Top Header */}
                <header className="bg-white shadow-sm border-b h-16 flex items-center justify-between px-4 sm:px-6 z-10 shrink-0">
                    <div className="flex items-center gap-4">
                        <button 
                            className="md:hidden text-gray-600 hover:text-gray-900"
                            onClick={() => setSidebarOpen(true)}
                        >
                            <Menu size={24} />
                        </button>
                        <h1 className="text-xl font-bold text-gray-800">{getPageTitle()}</h1>
                    </div>
                    <div className="hidden sm:block text-indigo-800 font-bold">
                        Chennakesava Boys Hostel
                    </div>
                    <div className="text-sm text-gray-500">
                        Welcome back!
                    </div>
                </header>

                {/* Page Content */}
                <div className="flex-1 overflow-y-auto p-4 sm:p-6">
                    <Outlet />
                </div>
            </main>
        </div>
    );
};

export default StudentLayout;
