import React, { useEffect, useState, useContext } from 'react';
import axios from 'axios';
import { AuthContext } from '../context/AuthContext';
import { LogOut, Download } from 'lucide-react';

const AdminDashboard = () => {
  const { user, logout } = useContext(AuthContext);
  const [stats, setStats] = useState(null);
  const [menus, setMenus] = useState([]);
  const [targetDate, setTargetDate] = useState(new Date().toISOString().split('T')[0]);

  // Menu composer state
  const [composer, setComposer] = useState({ meal_slot: 'breakfast', meal_type: 'veg', items: '' });
  const [msg, setMsg] = useState('');

  // Register Student state
  const [regData, setRegData] = useState({ name: '', email: '', meal_preference: 'veg' });
  const [regMsg, setRegMsg] = useState('');
  const [regErr, setRegErr] = useState('');
  const [registering, setRegistering] = useState(false);

  // Change Password state
  const [passData, setPassData] = useState({ currentPassword: '', newPassword: '', confirmPassword: '' });
  const [passMsg, setPassMsg] = useState('');
  const [passErr, setPassErr] = useState('');
  const [changingPass, setChangingPass] = useState(false);

  useEffect(() => {
    fetchDashboard();
    fetchMenus();
  }, [targetDate]);

  const fetchDashboard = async () => {
    try {
      const res = await axios.get(`/api/admin/dashboard?date=${targetDate}`);
      setStats(res.data);
    } catch (err) {
      console.error('Failed to load dashboard:', err);
    }
  };

  const fetchMenus = async () => {
    try {
      const res = await axios.get(`/api/admin/menu`);
      setMenus(res.data);
    } catch (err) {
      console.error('Failed to load menus:', err);
    }
  };

  const handleMenuSubmit = async (e) => {
    e.preventDefault();
    try {
      await axios.post(`/api/admin/menu`, {
        date: targetDate,
        ...composer
      });
      setMsg('Menu saved!');
      setTimeout(() => setMsg(''), 3000);
      fetchMenus();
    } catch (err) {
      alert(err.response?.data?.error || 'Failed to save menu');
    }
  };

  const handleExport = () => {
    const month = targetDate.substring(0, 7);
    window.location.href = `/api/admin/reports/export?month=${month}`;
  };

  const handleRegisterStudent = async (e) => {
    e.preventDefault();
    setRegMsg(''); setRegErr(''); setRegistering(true);
    try {
        const res = await axios.post(`/api/admin/register-student`, regData, 
            { withCredentials: true, headers: { Authorization: `Bearer ${localStorage.getItem('token')}` } }
        );
        setRegMsg(res.data.message);
        setRegData({ name: '', email: '', meal_preference: 'veg' });
    } catch (err) {
        setRegErr(err.response?.data?.error || 'Failed to register student');
    } finally {
        setRegistering(false);
    }
  };

  const handlePasswordChange = async (e) => {
    e.preventDefault();
    setPassMsg(''); setPassErr('');
    
    if (passData.newPassword !== passData.confirmPassword) return setPassErr('New passwords do not match');
    if (passData.newPassword.length < 6) return setPassErr('Password must be at least 6 characters');

    setChangingPass(true);
    try {
        const res = await axios.post(`/api/auth/change-password`, {
            currentPassword: passData.currentPassword,
            newPassword: passData.newPassword
        }, { withCredentials: true, headers: { Authorization: `Bearer ${localStorage.getItem('token')}` } });
        
        setPassMsg(res.data.message || 'Password updated successfully');
        setPassData({ currentPassword: '', newPassword: '', confirmPassword: '' });
    } catch (err) {
        setPassErr(err.response?.data?.error || 'Failed to change password');
    } finally {
        setChangingPass(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 p-6">
      <div className="max-w-6xl mx-auto space-y-6">

        {/* Header */}
        <header className="flex items-center justify-between bg-white p-4 rounded shadow border-t-4 border-purple-600">
          <div>
            <h1 className="text-xl font-bold text-gray-800">Admin Dashboard - Hostel Food System</h1>
            <p className="text-sm text-gray-500">Welcome, Administrator</p>
          </div>
          <div className="flex gap-4 items-center">
            <input
              type="date"
              value={targetDate}
              onChange={e => setTargetDate(e.target.value)}
              className="border p-2 rounded text-sm outline-none"
            />
            <button onClick={logout} className="flex items-center text-red-600 hover:text-red-800 font-medium">
              <LogOut size={20} className="mr-1" /> Logout
            </button>
          </div>
        </header>

        {stats && (
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">

            {/* Counts */}
            <div className="bg-white p-6 rounded shadow border-l-4 border-blue-500">
              <h2 className="text-lg font-bold mb-4 text-blue-900 border-b pb-2">Breakfast Headcount</h2>
              <div className="flex justify-between items-center mb-2">
                <span className="text-gray-600">Total Expected:</span>
                <span className="text-2xl font-bold">{stats.expectedCounts.breakfast.total}</span>
              </div>
              <div className="text-sm text-gray-500 flex justify-between">
                <span>Veg: <span className="font-bold text-green-600">{stats.expectedCounts.breakfast.veg}</span></span>
                <span>Non-Veg: <span className="font-bold text-red-600">{stats.expectedCounts.breakfast.nonVeg}</span></span>
              </div>
            </div>

            <div className="bg-white p-6 rounded shadow border-l-4 border-orange-500">
              <h2 className="text-lg font-bold mb-4 text-orange-900 border-b pb-2">Lunch Headcount</h2>
              <div className="flex justify-between items-center mb-2">
                <span className="text-gray-600">Total Expected:</span>
                <span className="text-2xl font-bold">{stats.expectedCounts.lunch.total}</span>
              </div>
              <div className="text-sm text-gray-500 flex justify-between">
                <span>Veg: <span className="font-bold text-green-600">{stats.expectedCounts.lunch.veg}</span></span>
                <span>Non-Veg: <span className="font-bold text-red-600">{stats.expectedCounts.lunch.nonVeg}</span></span>
              </div>
            </div>

            <div className="bg-white p-6 rounded shadow border-l-4 border-indigo-500">
              <h2 className="text-lg font-bold mb-4 text-indigo-900 border-b pb-2">Dinner Headcount</h2>
              <div className="flex justify-between items-center mb-2">
                <span className="text-gray-600">Total Expected:</span>
                <span className="text-2xl font-bold">{stats.expectedCounts.dinner.total}</span>
              </div>
              <div className="text-sm text-gray-500 flex justify-between">
                <span>Veg: <span className="font-bold text-green-600">{stats.expectedCounts.dinner.veg}</span></span>
                <span>Non-Veg: <span className="font-bold text-red-600">{stats.expectedCounts.dinner.nonVeg}</span></span>
              </div>
            </div>

          </div>
        )}

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 align-top">

          {/* Main Menu Editor */}
          <section className="bg-white p-6 rounded shadow col-span-2">
            <h2 className="text-lg font-bold mb-4">Post & Edit Menu for {targetDate}</h2>
            {msg && <div className="text-green-600 font-bold mb-4 bg-green-50 p-2 rounded">{msg}</div>}

            <form onSubmit={handleMenuSubmit} className="space-y-4">
              <div className="flex gap-4">
                <div className="flex-1">
                  <label className="block text-sm font-medium mb-1">Meal Slot</label>
                  <select value={composer.meal_slot} onChange={e => setComposer({ ...composer, meal_slot: e.target.value })} className="w-full border rounded p-2 outline-none">
                    <option value="breakfast">Breakfast</option>
                    <option value="lunch">Lunch</option>
                    <option value="dinner">Dinner</option>
                  </select>
                </div>
                <div className="flex-1">
                  <label className="block text-sm font-medium mb-1">Type</label>
                  <select value={composer.meal_type} onChange={e => setComposer({ ...composer, meal_type: e.target.value })} className="w-full border rounded p-2 outline-none">
                    <option value="veg">Vegetarian (Veg)</option>
                    <option value="non-veg">Non-Vegetarian</option>
                  </select>
                </div>
              </div>
              <div>
                <label className="block text-sm font-medium mb-1">Food Items</label>
                <textarea
                  value={composer.items}
                  onChange={e => setComposer({ ...composer, items: e.target.value })}
                  placeholder="e.g. Rice, Dal, Sabzi, Curd"
                  className="w-full border rounded p-2 outline-none" rows="3" required
                />
              </div>
              <button type="submit" className="bg-purple-600 hover:bg-purple-700 text-white w-full py-2 rounded font-bold transition">
                Publish Menu Updates
              </button>
            </form>

            <h3 className="font-bold mt-8 mb-3 text-gray-700">Currently Saved Menu for {targetDate}</h3>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              {menus.filter(m => m.date === targetDate).map(m => (
                <div key={m.id} className="border p-3 rounded bg-gray-50 relative">
                  <span className="font-bold capitalize block">{m.meal_slot} ({m.meal_type})</span>
                  <p className="text-gray-700 mt-1 text-sm">{m.items}</p>
                  {m.is_locked ? (
                    <span className="absolute top-2 right-2 text-xs bg-red-100 text-red-700 px-2 py-1 rounded font-bold">LOCKED</span>
                  ) : (
                    <span className="absolute top-2 right-2 text-xs bg-green-100 text-green-700 px-2 py-1 rounded font-bold">EDITABLE</span>
                  )}
                </div>
              ))}
            </div>
          </section>

          {/* Opt-out Lists & Reports */}
          <section className="space-y-6">
            <div className="bg-white p-6 rounded shadow">
              <h2 className="text-lg font-bold mb-4">Export Reports</h2>
              <p className="text-sm text-gray-600 mb-4">Download Excel spreadsheet of opt-outs and food wastage savings for {targetDate.substring(0, 7)}.</p>
              <button onClick={handleExport} className="w-full flex items-center justify-center gap-2 bg-green-600 hover:bg-green-700 text-white py-2 rounded font-bold transition">
                <Download size={18} /> Export Excel Report
              </button>
            </div>

            <div className="bg-white p-6 rounded shadow">
              <h2 className="text-lg font-bold mb-4">Today's Opt-Outs ({stats?.optOutLists?.length || 0})</h2>
              <div className="max-h-64 overflow-y-auto space-y-3">
                {stats?.optOutLists && stats.optOutLists.length > 0 ? (
                  stats.optOutLists.map(o => (
                    <div key={o.id} className="border-b pb-2 text-sm">
                      <span className="font-bold block">{o.name} <span className="text-xs text-gray-500">[{o.meal_preference}]</span></span>
                      <div className="text-xs text-gray-600 mt-1">
                        Skipped:
                        {o.breakfast ? ' [B]' : ''}
                        {o.lunch ? ' [L]' : ''}
                        {o.dinner ? ' [D]' : ''}
                      </div>
                      {o.reason && <div className="text-xs text-gray-500 italic mt-0.5 mt-1 border-l-2 pl-2">Reason: {o.reason}</div>}
                    </div>
                  ))
                ) : (
                  <p className="text-sm text-gray-500 italic">No one has opted out today.</p>
                )}
              </div>
            </div>
          </section>

        </div>

        {/* Admin Settings & Registration Row */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 pb-12">
            
            {/* Register Student */}
            <div className="bg-white p-6 rounded shadow border-t-4 border-indigo-500">
                <h2 className="text-lg font-bold mb-4">Register New Student</h2>
                {regMsg && <div className="bg-green-100 text-green-700 p-2 mb-4 rounded text-sm">{regMsg}</div>}
                {regErr && <div className="bg-red-100 text-red-700 p-2 mb-4 rounded text-sm">{regErr}</div>}
                <form onSubmit={handleRegisterStudent} className="space-y-4">
                    <div>
                        <label className="block text-sm font-medium mb-1">Full Name</label>
                        <input type="text" required className="w-full border rounded p-2 text-sm outline-none" value={regData.name} onChange={e => setRegData({...regData, name: e.target.value})} />
                    </div>
                    <div>
                        <label className="block text-sm font-medium mb-1">Email Address</label>
                        <input type="email" required className="w-full border rounded p-2 text-sm outline-none" value={regData.email} onChange={e => setRegData({...regData, email: e.target.value})} />
                    </div>
                    <div>
                        <label className="block text-sm font-medium mb-1">Default Meal Preference</label>
                        <select className="w-full border rounded p-2 text-sm outline-none" value={regData.meal_preference} onChange={e => setRegData({...regData, meal_preference: e.target.value})}>
                            <option value="veg">Vegetarian (Veg)</option>
                            <option value="non-veg">Non-Vegetarian</option>
                        </select>
                    </div>
                    <button type="submit" disabled={registering} className="bg-indigo-600 hover:bg-indigo-700 text-white w-full py-2 rounded font-bold transition disabled:bg-indigo-400">
                        {registering ? 'Registering...' : 'Register & Email Password'}
                    </button>
                </form>
            </div>

            {/* Change Admin Password */}
            <div className="bg-white p-6 rounded shadow border-t-4 border-gray-800">
                <h2 className="text-lg font-bold mb-4">Change Admin Password</h2>
                {passMsg && <div className="bg-green-100 text-green-700 p-2 mb-4 rounded text-sm">{passMsg}</div>}
                {passErr && <div className="bg-red-100 text-red-700 p-2 mb-4 rounded text-sm">{passErr}</div>}
                <form onSubmit={handlePasswordChange} className="space-y-4">
                    <div>
                        <label className="block text-sm font-medium mb-1">Current Password</label>
                        <input type="password" required className="w-full border rounded p-2 text-sm outline-none" value={passData.currentPassword} onChange={e => setPassData({...passData, currentPassword: e.target.value})} />
                    </div>
                    <div>
                        <label className="block text-sm font-medium mb-1">New Password</label>
                        <input type="password" required className="w-full border rounded p-2 text-sm outline-none" value={passData.newPassword} onChange={e => setPassData({...passData, newPassword: e.target.value})} />
                    </div>
                    <div>
                        <label className="block text-sm font-medium mb-1">Confirm New Password</label>
                        <input type="password" required className="w-full border rounded p-2 text-sm outline-none" value={passData.confirmPassword} onChange={e => setPassData({...passData, confirmPassword: e.target.value})} />
                    </div>
                    <button type="submit" disabled={changingPass} className="bg-gray-800 hover:bg-gray-900 text-white w-full py-2 rounded font-bold transition disabled:bg-gray-500">
                        {changingPass ? 'Updating...' : 'Update Password'}
                    </button>
                </form>
            </div>

        </div>

      </div>
    </div>
  );
};

export default AdminDashboard;
