import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { DollarSign, FileText, CheckCircle, AlertCircle, Info } from 'lucide-react';

const FeeStatusStudent = () => {
    const [fees, setFees] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState('');

    useEffect(() => {
        const fetchFees = async () => {
            try {
                const res = await axios.get(`http://${window.location.hostname}:5000/api/student/fee_status`, { withCredentials: true });
                setFees(res.data);
            } catch (err) {
                console.error("Fee fetch error", err);
                setError('Failed to load fee status.');
            } finally {
                setLoading(false);
            }
        };
        fetchFees();
    }, []);

    if (loading) return <div className="flex items-center justify-center p-8 text-indigo-600 font-bold">Loading Fee Status...</div>;
    if (error) return <div className="bg-red-50 text-red-600 p-4 rounded shadow">{error}</div>;

    const currentFee = fees.length > 0 ? fees[0] : null;

    return (
        <div className="max-w-5xl mx-auto space-y-6">
            
            <div className="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden">
                <div className="border-b border-gray-100 p-4 bg-gray-50/50 flex items-center gap-2">
                    <DollarSign className="text-indigo-500" size={20} />
                    <h3 className="font-bold text-gray-800">Current Fee Status</h3>
                </div>
                <div className="p-6">
                    {currentFee ? (
                        <div className="flex flex-col md:flex-row items-center gap-6 justify-between">
                            <div>
                                <h4 className="text-xl font-bold mb-1">Fee for {currentFee.month} {currentFee.year}</h4>
                                <p className="text-gray-500 flex items-center gap-1">
                                    <Info size={14}/> Generated on: {currentFee.created_at}
                                </p>
                            </div>
                            <div className="flex items-center gap-4">
                                <div className="text-right">
                                    <div className="text-sm text-gray-500">Total Amount</div>
                                    <div className="text-2xl font-bold text-gray-800">₹{currentFee.amount}</div>
                                </div>
                                <div className="h-12 w-px bg-gray-200"></div>
                                <div className="text-right">
                                    <div className="text-sm text-gray-500">Status</div>
                                    <div className={`px-3 py-1 rounded-full text-sm font-bold mt-1 inline-flex items-center gap-1
                                        ${currentFee.status === 'paid' ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'}`}
                                    >
                                        {currentFee.status === 'paid' ? <CheckCircle size={14}/> : <AlertCircle size={14}/>}
                                        {currentFee.status.toUpperCase()}
                                    </div>
                                </div>
                            </div>
                        </div>
                    ) : (
                        <p className="text-gray-500 text-center py-4">No fee records found.</p>
                    )}
                </div>
            </div>

            <div className="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden">
                <div className="border-b border-gray-100 p-4 bg-gray-50/50 flex items-center gap-2">
                    <FileText className="text-indigo-500" size={20} />
                    <h3 className="font-bold text-gray-800">Fee History</h3>
                </div>
                <div className="p-0">
                    {fees.length === 0 ? (
                        <p className="text-gray-500 text-center py-6">No historical records.</p>
                    ) : (
                        <div className="overflow-x-auto">
                            <table className="w-full text-left border-collapse">
                                <thead>
                                    <tr className="bg-gray-50 border-b text-gray-500 text-sm">
                                        <th className="p-4 font-semibold">Month/Year</th>
                                        <th className="p-4 font-semibold">Amount</th>
                                        <th className="p-4 font-semibold">Status</th>
                                        <th className="p-4 font-semibold">Generated Date</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {fees.map((f, idx) => (
                                        <tr key={idx} className="border-b hover:bg-gray-50">
                                            <td className="p-4 font-medium text-gray-800">{f.month} {f.year}</td>
                                            <td className="p-4 font-bold text-gray-700">₹{f.amount}</td>
                                            <td className="p-4">
                                                <span className={`px-2 py-1 rounded text-xs font-bold uppercase
                                                    ${f.status === 'paid' ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'}`}
                                                >
                                                    {f.status}
                                                </span>
                                            </td>
                                            <td className="p-4 text-sm text-gray-500">{f.created_at}</td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        </div>
                    )}
                </div>
            </div>

        </div>
    );
};

export default FeeStatusStudent;
