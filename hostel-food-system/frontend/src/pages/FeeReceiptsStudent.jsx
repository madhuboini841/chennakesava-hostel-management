import React, { useState, useEffect, useContext } from 'react';
import axios from 'axios';
import { AuthContext } from '../context/AuthContext';
import { Download, Receipt } from 'lucide-react';

const FeeReceiptsStudent = () => {
    const { user } = useContext(AuthContext);
    const [receipts, setReceipts] = useState([]);
    
    const API_BASE = 'http://localhost:5000/api/receipts';

    useEffect(() => {
        if (user && user.id) {
            fetchMyReceipts();
        }
    }, [user]);

    const fetchMyReceipts = async () => {
        try {
            const res = await axios.get(`http://${window.location.hostname}:5000/api/student/receipts`, { withCredentials: true });
            setReceipts(res.data);
        } catch (err) {
            console.error("Failed to fetch receipts", err);
        }
    };

    const handleDownload = (id) => {
        window.open(`${API_BASE}/download/${id}`, "_blank");
    };

    return (
        <div className="max-w-5xl mx-auto space-y-6">
            
            <div className="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden">
                <div className="border-b border-gray-100 p-4 bg-gray-50/50 flex items-center justify-between">
                    <div className="flex items-center gap-2">
                        <Receipt className="text-indigo-500" size={20} />
                        <h3 className="font-bold text-gray-800">Receipts History</h3>
                    </div>
                    <span className="text-sm bg-indigo-100 text-indigo-800 py-1 px-3 rounded-full font-bold">{receipts.length} Total</span>
                </div>
                <div className="overflow-x-auto">
                    <table className="w-full text-left border-collapse">
                        <thead>
                            <tr className="bg-gray-50 border-b text-gray-500 text-sm">
                                <th className="p-4 font-semibold">Receipt No</th>
                                <th className="p-4 font-semibold">Date & Time</th>
                                <th className="p-4 font-semibold">Amount</th>
                                <th className="p-4 font-semibold">Type/Mode</th>
                                <th className="p-4 font-semibold text-center">Download</th>
                            </tr>
                        </thead>
                        <tbody>
                            {(!Array.isArray(receipts) || receipts.length === 0) ? (
                                <tr><td colSpan="5" className="p-8 text-center text-gray-500">No receipts found.</td></tr>
                            ) : (
                                receipts.map(r => (
                                    <tr key={r.id} className="border-b hover:bg-gray-50 transition">
                                        <td className="p-4 font-bold text-indigo-700 whitespace-nowrap">{r.receipt_number}</td>
                                        <td className="p-4 text-sm text-gray-600 whitespace-nowrap">{new Date(r.created_at).toLocaleString()}</td>
                                        <td className="p-4 font-bold text-green-600">₹{r.amount}</td>
                                        <td className="p-4">
                                            <div className="text-sm text-gray-800">{r.payment_type}</div>
                                            <div className="text-xs text-gray-500">{r.payment_mode} • {r.period}</div>
                                        </td>
                                        <td className="p-4 flex justify-center">
                                            <button 
                                                onClick={() => handleDownload(r.id)} 
                                                className="flex items-center gap-2 bg-indigo-50 text-indigo-700 px-3 py-1.5 rounded-lg font-bold hover:bg-indigo-100 transition shadow-sm text-sm"
                                                title="Download PDF"
                                            >
                                                <Download size={16} /> PDF
                                            </button>
                                        </td>
                                    </tr>
                                ))
                            )}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    );
};

export default FeeReceiptsStudent;
