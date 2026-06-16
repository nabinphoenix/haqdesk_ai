"use client";

import { useState, useEffect } from "react";
import {
    Mail,
    Phone,
    MapPin,
    Globe,
    ShieldCheck,
    CreditCard,
    Award,
    Link as LinkIcon,
    Save,
    Search
} from "lucide-react";
import SocialIcon from "../ui/SocialIcon";

interface CustomerProfile {
    id: number;
    display_name: string;
    phone?: string | null;
    email?: string | null;
    avatar_url: string | null;
    notes: string | null;
    platforms: string[];
    linked_accounts: { id: number, platform: string, display_name: string }[];
}

interface CustomerSidebarProps {
    customerId: string | number;
    platform?: string;
}

export default function CustomerSidebar({ customerId, platform }: CustomerSidebarProps) {
    const [profile, setProfile] = useState<CustomerProfile | null>(null);
    const [notes, setNotes] = useState("");
    const [isSaving, setIsSaving] = useState(false);
    const [conversations, setConversations] = useState<any[]>([]);
    const [showLinkModal, setShowLinkModal] = useState(false);
    
    // Manual link form state
    const [manualName, setManualName] = useState("");
    const [manualPhone, setManualPhone] = useState("");
    const [manualEmail, setManualEmail] = useState("");
    const [isLinking, setIsLinking] = useState(false);

    useEffect(() => {
        if (customerId) {
            fetchCustomerData();
            fetchConversations();
        }
    }, [customerId]);

    const fetchCustomerData = async () => {
        try {
            const token = localStorage.getItem("token");
            const res = await fetch(`http://localhost:8000/api/v1/customers/${customerId}`, {
                headers: { 'Authorization': `Bearer ${token}` }
            });
            if (res.ok) {
                const data = await res.json();
                setProfile(data);
                setNotes(data.notes || "");
            }
        } catch (error) {
            console.error("Failed to fetch customer", error);
        }
    };

    const fetchConversations = async () => {
        try {
            const token = localStorage.getItem("token");
            const res = await fetch(`http://localhost:8000/api/v1/customers/${customerId}/conversations`, {
                headers: { 'Authorization': `Bearer ${token}` }
            });
            if (res.ok) {
                setConversations(await res.json());
            }
        } catch (error) {
            console.error("Failed to fetch conversations", error);
        }
    };

    const handleSaveNotes = async () => {
        setIsSaving(true);
        try {
            const token = localStorage.getItem("token");
            await fetch(`http://localhost:8000/api/v1/customers/${customerId}/notes`, {
                method: "POST",
                headers: { 
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ note: notes })
            });
        } catch (error) {
            console.error("Failed to save notes", error);
        }
        setIsSaving(false);
    };

    const handleManualLink = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!manualName.trim()) return;
        
        setIsLinking(true);
        try {
            const token = localStorage.getItem("token");
            const res = await fetch(
                `http://localhost:8000/api/v1/customers/${customerId}/create_and_link`,
                {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ 
                        display_name: manualName,
                        phone: manualPhone || null,
                        email: manualEmail || null,
                        token 
                    })
                }
            );
            if (res.ok) {
                setShowLinkModal(false);
                setManualName("");
                setManualPhone("");
                setManualEmail("");
                fetchCustomerData(); // refresh sidebar
                // Refresh main conversations list if available (optional)
                window.dispatchEvent(new Event('customerLinked'));
            }
        } catch (e) {
            console.error(e);
        } finally {
            setIsLinking(false);
        }
    };

    if (!profile) return <div className="p-8 text-center text-sm text-slate-400">Loading profile...</div>;

    return (
        <div className="w-full h-full flex flex-col bg-transparent overflow-hidden relative font-jakarta">
            {/* Header */}
            <div className="p-6 pb-4 border-b border-surface-border text-center relative">
                <div className="w-16 h-16 rounded-2xl bg-[#6D4AE2]/20 border border-surface-border flex items-center justify-center font-black text-2xl text-[#818CF8] shadow-sm mb-3 mx-auto overflow-hidden relative">
                    {profile.avatar_url ? (
                        <img src={profile.avatar_url} alt="Avatar" className="w-full h-full object-cover" />
                    ) : (
                        profile.display_name?.substring(0, 1).toUpperCase() || "C"
                    )}
                    {/* Primary Platform Badge */}
                    <div className="absolute -bottom-1 -right-1 w-5 h-5 rounded-md bg-background shadow-md flex items-center justify-center p-1 border border-surface-border">
                        <SocialIcon platform={platform || profile.platforms[0] as any} className="w-full h-full" />
                    </div>
                </div>

                <h2 className="text-[15px] font-bold text-white tracking-tight text-center">
                    {profile.display_name || "Customer"}
                </h2>
                <p className="text-[11px] text-gray-400 text-center mt-0.5 uppercase tracking-wider">
                    {(platform || profile.platforms[0])} · Customer
                </p>
                
                {/* Platform Badges */}
                <div className="flex items-center justify-center gap-1">
                    {profile.platforms.map(p => (
                        <div key={p} className="w-6 h-6 rounded-md bg-white/5 flex items-center justify-center border border-surface-border">
                            <SocialIcon platform={p as any} className="w-4 h-4" />
                        </div>
                    ))}
                </div>
            </div>

            <div className="flex-1 overflow-y-auto custom-scrollbar p-6 space-y-6">
                
                {/* Contact Info (if available) */}
                {(profile.phone || profile.email) && (
                    <div className="space-y-3">
                        <span className="text-[10px] font-black uppercase tracking-[0.2em] text-[#818CF8]">Contact Info</span>
                        <div className="space-y-2">
                            {profile.phone && (
                                <div className="flex items-center gap-3 p-3 rounded-xl bg-white/5 border border-surface-border">
                                    <Phone className="w-4 h-4 text-gray-400" />
                                    <span className="text-[12px] font-medium text-white">{profile.phone}</span>
                                </div>
                            )}
                            {profile.email && (
                                <div className="flex items-center gap-3 p-3 rounded-xl bg-white/5 border border-surface-border">
                                    <Mail className="w-4 h-4 text-gray-400" />
                                    <span className="text-[12px] font-medium text-white truncate">{profile.email}</span>
                                </div>
                            )}
                        </div>
                    </div>
                )}
                
                {/* Linked Accounts */}
                {profile.linked_accounts.length > 0 && (
                    <div className="space-y-3">
                        <span className="text-[10px] font-black uppercase tracking-[0.2em] text-[#818CF8]">Linked Identities</span>
                        <div className="space-y-2">
                            {profile.linked_accounts.map(acc => (
                                <div key={acc.id} className="flex items-center gap-3 p-3 rounded-xl bg-white/5 border border-surface-border">
                                    <SocialIcon platform={acc.platform as any} className="w-5 h-5" />
                                    <span className="text-[11px] font-bold text-slate-900 dark:text-white">{acc.display_name}</span>
                                </div>
                            ))}
                        </div>
                    </div>
                )}

                {/* Notes Section */}
                <div className="space-y-3">
                    <div className="flex items-center justify-between">
                        <span className="text-[10px] font-black uppercase tracking-[0.2em] text-[#818CF8]">Agent Notes</span>
                        <button onClick={handleSaveNotes} disabled={isSaving} className="text-[#818CF8] hover:text-slate-900 dark:text-white transition-colors">
                            {isSaving ? (
                                <div className="w-3.5 h-3.5 border-2 border-[#818CF8] border-t-transparent rounded-full animate-spin" />
                            ) : (
                                <Save size={14} />
                            )}
                        </button>
                    </div>
                    <textarea 
                        value={notes}
                        onChange={(e) => setNotes(e.target.value)}
                        placeholder="Add notes about this customer..."
                        className="w-full h-24 p-3 rounded-xl bg-white/5 border border-surface-border text-[12px] text-slate-900 dark:text-white placeholder-slate-500 font-medium outline-none focus:bg-white/[0.08] focus:border-[#818CF8]/30 transition-all resize-none"
                    />
                </div>

                {/* Conversation History */}
                <div className="space-y-3">
                    <span className="text-[10px] font-black uppercase tracking-[0.2em] text-[#818CF8]">History ({conversations.length})</span>
                    <div className="space-y-2">
                        {conversations.map(conv => (
                            <div key={conv.id} className="p-3 rounded-xl border border-surface-border hover:bg-white/5 transition-all cursor-pointer">
                                <div className="flex justify-between items-center mb-1">
                                    <div className="flex items-center gap-2">
                                        <SocialIcon platform={conv.platform as any} className="w-3 h-3" />
                                        <span className="text-[10px] font-bold text-slate-900 dark:text-white uppercase">Conv #{conv.id}</span>
                                    </div>
                                    <span className="text-[9px] font-bold text-slate-400">{new Date(conv.time).toLocaleDateString()}</span>
                                </div>
                                <p className="text-[11px] text-slate-400 truncate">{conv.last_message || "Started"}</p>
                            </div>
                        ))}
                    </div>
                </div>
            </div>

            {/* ACTION FOOTER */}
            <div className="p-6 border-t border-surface-border bg-transparent">
                <button 
                    onClick={() => setShowLinkModal(true)}
                    className="w-full py-4 border border-[#6D4AE2] text-white hover:bg-[#6D4AE2] hover:shadow-lg rounded-2xl text-[11px] font-black uppercase tracking-[0.3em] transition-all flex items-center justify-center gap-3 active:scale-95 bg-[#6D4AE2]/10"
                >
                    <LinkIcon size={16} strokeWidth={2.5} />
                    Link Account
                </button>
            </div>

            {/* Link Account Modal Overlay */}
            {showLinkModal && (
                <div className="absolute inset-0 bg-background/95 backdrop-blur-md z-50 flex flex-col p-6 border border-surface-border rounded-[1.5rem] overflow-y-auto custom-scrollbar">
                    <div className="flex justify-between items-center mb-5 shrink-0">
                        <h3 className="text-sm font-black text-white uppercase tracking-wider">Create & Link</h3>
                        <button
                            onClick={() => { setShowLinkModal(false); setManualName(""); setManualPhone(""); setManualEmail(""); }}
                            className="text-slate-400 hover:text-white font-bold text-lg"
                        >
                            &times;
                        </button>
                    </div>

                    <p className="text-[11px] text-gray-400 mb-5 text-center leading-relaxed shrink-0">
                        Enter details to create a master customer record and link it to this social account.
                    </p>

                    <form onSubmit={handleManualLink} className="space-y-4 shrink-0">
                        <div>
                            <label className="block text-[10px] font-black uppercase tracking-wider text-gray-400 mb-1.5 ml-1">
                                Full Name <span className="text-red-400">*</span>
                            </label>
                            <input
                                type="text"
                                required
                                value={manualName}
                                onChange={(e) => setManualName(e.target.value)}
                                placeholder="e.g. John Doe"
                                className="w-full p-3 rounded-xl border border-white/10 bg-white/5 text-white text-[13px] placeholder-gray-500 focus:border-purple-500 focus:outline-none transition-all"
                            />
                        </div>
                        
                        <div>
                            <label className="block text-[10px] font-black uppercase tracking-wider text-gray-400 mb-1.5 ml-1">
                                Phone Number (Optional)
                            </label>
                            <input
                                type="tel"
                                value={manualPhone}
                                onChange={(e) => setManualPhone(e.target.value)}
                                placeholder="+1 234 567 890"
                                className="w-full p-3 rounded-xl border border-white/10 bg-white/5 text-white text-[13px] placeholder-gray-500 focus:border-purple-500 focus:outline-none transition-all"
                            />
                        </div>
                        
                        <div>
                            <label className="block text-[10px] font-black uppercase tracking-wider text-gray-400 mb-1.5 ml-1">
                                Email Address (Optional)
                            </label>
                            <input
                                type="email"
                                value={manualEmail}
                                onChange={(e) => setManualEmail(e.target.value)}
                                placeholder="john@example.com"
                                className="w-full p-3 rounded-xl border border-white/10 bg-white/5 text-white text-[13px] placeholder-gray-500 focus:border-purple-500 focus:outline-none transition-all"
                            />
                        </div>

                        <div className="pt-2">
                            <button 
                                type="submit"
                                disabled={isLinking || !manualName.trim()}
                                className="w-full py-3.5 bg-[#6D4AE2] text-white rounded-xl text-[12px] font-bold uppercase tracking-wider disabled:opacity-50 disabled:cursor-not-allowed hover:bg-[#5b3cc4] transition-all flex justify-center items-center gap-2"
                            >
                                {isLinking ? (
                                    <div className="w-4 h-4 border-2 border-white/20 border-t-white rounded-full animate-spin" />
                                ) : (
                                    <>
                                        <Save size={14} />
                                        Save & Link
                                    </>
                                )}
                            </button>
                        </div>
                    </form>
                </div>
            )}
        </div>
    );
}



