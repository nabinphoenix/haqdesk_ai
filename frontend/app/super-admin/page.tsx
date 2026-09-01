'use client';

import { type ReactNode, useCallback, useEffect, useMemo, useState } from 'react';
import { useRouter } from 'next/navigation';
import { Activity, BarChart3, Building2, CheckCircle2, CircleAlert, Database, FileText, Mail, MessageSquare, Pencil, Plus, RefreshCw, Search, ServerCog, ShieldCheck, Trash2, UserCog, Users, X } from 'lucide-react';
import { fetchWithAuth } from '@/lib/api';

type Tab = 'overview' | 'businesses' | 'users' | 'analytics' | 'system';
type Dashboard = {
  stats: { key: string; label: string; value: number; change: string }[];
  businesses: DashboardBusiness[];
  recent_activity: ActivityItem[];
  database_stats: { label: string; value: number }[];
  system_health: { label: string; status: string; detail: string }[];
};
type DashboardBusiness = { id: number; name: string; owner: string; users: number; agents: number; messages: number; joined: string | null };
type Business = {
  id: number; name: string; owner_email?: string | null; email?: string | null; phone?: string | null; website?: string | null; description?: string | null;
  is_active: boolean; user_count: number; message_count: number; conversation_count: number; created_at: string | null;
};
type ManagedUser = { id: number; name: string; email: string; role: string; status: string; business_id: number | null; business_name: string | null; created_at: string | null };
type ActivityItem = { action: string; target: string; type: string; timestamp: string | null };
type Analytics = {
  totals: { businesses: number; active_businesses: number; users: number; messages_in_period: number; conversations_in_period: number; customers: number; connected_integrations: number; knowledge_documents: number };
  channels: { platform: string; messages: number }[];
  businesses: { id: number; name: string; is_active: boolean; users: number; conversations: number; messages: number; customers: number; integrations: number; ai_drafts: number }[];
  data_note: string;
};
type BusinessForm = { name: string; email: string; phone: string; website: string; description: string; owner_email: string };
type UserForm = { name: string; email: string; password: string; business_id: string; role: string };

const emptyBusiness: BusinessForm = { name: '', email: '', phone: '', website: '', description: '', owner_email: '' };
const emptyUser: UserForm = { name: '', email: '', password: '', business_id: '', role: 'agent' };
function timeAgo(value: string | null) {
  if (!value) return 'Unknown time';
  const seconds = Math.max(0, Math.floor((Date.now() - new Date(value).getTime()) / 1000));
  if (seconds < 60) return seconds + 's ago';
  if (seconds < 3600) return Math.floor(seconds / 60) + 'm ago';
  if (seconds < 86400) return Math.floor(seconds / 3600) + 'h ago';
  return Math.floor(seconds / 86400) + 'd ago';
}

function dateLabel(value: string | null) { return value ? new Date(value).toLocaleDateString() : '—'; }

async function apiError(response: Response, fallback: string) {
  try { const body = await response.json(); return body.detail || fallback; } catch { return fallback; }
}

export default function SuperAdminDashboard() {
  const router = useRouter();
  const [tab, setTab] = useState<Tab>('overview');
  const [dashboard, setDashboard] = useState<Dashboard | null>(null);
  const [businesses, setBusinesses] = useState<Business[]>([]);
  const [users, setUsers] = useState<ManagedUser[]>([]);
  const [analytics, setAnalytics] = useState<Analytics | null>(null);
  const [analyticsDays, setAnalyticsDays] = useState(30);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');
  const [notice, setNotice] = useState('');
  const [query, setQuery] = useState('');
  const [showBusinessForm, setShowBusinessForm] = useState(false);
  const [showUserForm, setShowUserForm] = useState(false);
  const [businessForm, setBusinessForm] = useState<BusinessForm>(emptyBusiness);
  const [userForm, setUserForm] = useState<UserForm>(emptyUser);
  const [editingBusiness, setEditingBusiness] = useState<Business | null>(null);
  const [editingUser, setEditingUser] = useState<ManagedUser | null>(null);
  const [inviteBusiness, setInviteBusiness] = useState<Business | null>(null);
  const [inviteEmail, setInviteEmail] = useState('');
  const [showTeamInvitation, setShowTeamInvitation] = useState(false);
  const [teamInvitationBusinessId, setTeamInvitationBusinessId] = useState('');
  const [teamInvitationEmail, setTeamInvitationEmail] = useState('');
  const [teamInvitationRole, setTeamInvitationRole] = useState('agent');
  const [deleteUser, setDeleteUser] = useState<ManagedUser | null>(null);
  const [confirmation, setConfirmation] = useState('');
  const [deleteBusiness, setDeleteBusiness] = useState<Business | null>(null);
  const [businessConfirmation, setBusinessConfirmation] = useState('');

  const loadData = useCallback(async (days: number) => {
    setLoading(true); setError('');
    try {
      const results = await Promise.all([
        fetchWithAuth('/api/v1/super-admin/dashboard'),
        fetchWithAuth('/api/v1/super-admin/businesses'),
        fetchWithAuth('/api/v1/super-admin/users'),
        fetchWithAuth('/api/v1/super-admin/analytics?days=' + days),
      ]);
      if (results.some((result) => result.status === 401 || result.status === 403)) { router.replace('/inbox'); return; }
      if (results.some((result) => !result.ok)) throw new Error('One or more platform reports could not be loaded.');
      const data = await Promise.all(results.map((result) => result.json()));
      setDashboard(data[0]); setBusinesses(data[1]); setUsers(data[2]); setAnalytics(data[3]);
    } catch (loadError) {
      setError(loadError instanceof Error ? loadError.message : 'Could not load platform data.');
    } finally { setLoading(false); }
  }, [router]);

  useEffect(() => {
    if (localStorage.getItem('userRole') !== 'super_admin') { router.replace('/inbox'); return; }
    void loadData(analyticsDays);
  }, [analyticsDays, loadData, router]);

  const matchingBusinesses = useMemo(() => {
    const search = query.trim().toLowerCase();
    return search ? businesses.filter((item) => item.name.toLowerCase().includes(search) || (item.owner_email || '').toLowerCase().includes(search)) : businesses;
  }, [businesses, query]);
  const matchingUsers = useMemo(() => {
    const search = query.trim().toLowerCase();
    return search ? users.filter((item) => item.name.toLowerCase().includes(search) || item.email.toLowerCase().includes(search) || (item.business_name || '').toLowerCase().includes(search)) : users;
  }, [users, query]);

  function flash(message: string) { setNotice(message); window.setTimeout(() => setNotice(''), 4500); }
  function closeBusinessForm() { setEditingBusiness(null); setBusinessForm(emptyBusiness); setShowBusinessForm(false); }
  function closeUserForm() { setEditingUser(null); setUserForm(emptyUser); setShowUserForm(false); }
  function editBusiness(item: Business) { setEditingBusiness(item); setBusinessForm({ name: item.name, email: item.email || '', phone: item.phone || '', website: item.website || '', description: item.description || '', owner_email: '' }); setShowBusinessForm(true); }
  function editUser(item: ManagedUser) { setEditingUser(item); setUserForm({ name: item.name, email: item.email, password: '', business_id: item.business_id ? String(item.business_id) : '', role: item.role }); setShowUserForm(true); }

  async function saveBusiness(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault(); setSaving(true); setError('');
    const endpoint = editingBusiness ? '/api/v1/super-admin/businesses/' + editingBusiness.id : '/api/v1/super-admin/businesses';
    const body = editingBusiness ? { name: businessForm.name, email: businessForm.email || null, phone: businessForm.phone || null, website: businessForm.website || null, description: businessForm.description || null } : { ...businessForm, email: businessForm.email || null, phone: businessForm.phone || null, website: businessForm.website || null, description: businessForm.description || null, owner_email: businessForm.owner_email || null, send_owner_invitation: true };
    try {
      const response = await fetchWithAuth(endpoint, { method: editingBusiness ? 'PATCH' : 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) });
      if (!response.ok) throw new Error(await apiError(response, 'Business could not be saved.'));
      closeBusinessForm(); flash(editingBusiness ? 'Business profile updated.' : 'Business created. Owner invitation is ready when an email was provided.'); await loadData(analyticsDays);
    } catch (saveError) { setError(saveError instanceof Error ? saveError.message : 'Business could not be saved.'); } finally { setSaving(false); }
  }

  async function changeBusinessStatus(item: Business) {
    setSaving(true); setError('');
    try {
      const response = await fetchWithAuth('/api/v1/super-admin/businesses/' + item.id, { method: 'PATCH', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ is_active: !item.is_active }) });
      if (!response.ok) throw new Error(await apiError(response, 'Business status could not be changed.'));
      flash(item.is_active ? 'Business archived. Its data is retained.' : 'Business reactivated.'); await loadData(analyticsDays);
    } catch (updateError) { setError(updateError instanceof Error ? updateError.message : 'Business status could not be changed.'); } finally { setSaving(false); }
  }

  async function sendOwnerInvite(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!inviteBusiness) return;
    setSaving(true); setError('');
    try {
      const response = await fetchWithAuth('/api/v1/super-admin/businesses/' + inviteBusiness.id + '/owner-invitations', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ email: inviteEmail }) });
      if (!response.ok) throw new Error(await apiError(response, 'Owner invitation could not be created.'));
      const result = await response.json();
      if (!result.email_queued && navigator.clipboard) {
        await navigator.clipboard.writeText(result.invite_url);
        flash('Mail is not configured, so the registration link was copied.');
      } else { flash('Owner invitation email queued for delivery.'); }
      setInviteBusiness(null); setInviteEmail(''); await loadData(analyticsDays);
    } catch (inviteError) { setError(inviteError instanceof Error ? inviteError.message : 'Owner invitation could not be created.'); } finally { setSaving(false); }
  }

  async function sendTeamInvitation(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const businessId = Number(teamInvitationBusinessId);
    if (!businessId) return;
    setSaving(true); setError('');
    try {
      const response = await fetchWithAuth('/api/v1/super-admin/businesses/' + businessId + '/invitations', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ email: teamInvitationEmail, role: teamInvitationRole }) });
      if (!response.ok) throw new Error(await apiError(response, 'Team invitation could not be created.'));
      const result = await response.json();
      if (!result.email_queued && navigator.clipboard) {
        await navigator.clipboard.writeText(result.invite_url);
        flash('Mail is not configured, so the invitation link was copied.');
      } else { flash('Team invitation email queued for delivery.'); }
      setShowTeamInvitation(false); setTeamInvitationBusinessId(''); setTeamInvitationEmail(''); setTeamInvitationRole('agent'); await loadData(analyticsDays);
    } catch (inviteError) { setError(inviteError instanceof Error ? inviteError.message : 'Team invitation could not be created.'); } finally { setSaving(false); }
  }

  async function saveUser(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault(); setSaving(true); setError('');
    const editing = Boolean(editingUser);
    const body = editing ? { name: userForm.name, email: userForm.email, business_id: Number(userForm.business_id), role: userForm.role } : { ...userForm, business_id: Number(userForm.business_id) };
    try {
      const response = await fetchWithAuth(editing ? '/api/v1/super-admin/users/' + editingUser?.id : '/api/v1/super-admin/users', { method: editing ? 'PATCH' : 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) });
      if (!response.ok) throw new Error(await apiError(response, 'User could not be saved.'));
      closeUserForm(); flash(editing ? 'User access updated.' : 'User account created.'); await loadData(analyticsDays);
    } catch (saveError) { setError(saveError instanceof Error ? saveError.message : 'User could not be saved.'); } finally { setSaving(false); }
  }

  async function removeUser(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!deleteUser) return;
    setSaving(true); setError('');
    try {
      const response = await fetchWithAuth('/api/v1/super-admin/users/' + deleteUser.id, { method: 'DELETE', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ confirm_email: confirmation }) });
      if (!response.ok) throw new Error(await apiError(response, 'User could not be deleted.'));
      flash(deleteUser.name + ' was permanently deleted. Conversation history is retained.');
      setDeleteUser(null); setConfirmation(''); await loadData(analyticsDays);
    } catch (deleteError) { setError(deleteError instanceof Error ? deleteError.message : 'User could not be deleted.'); } finally { setSaving(false); }
  }

  async function removeBusiness(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!deleteBusiness) return;
    setSaving(true); setError('');
    try {
      const response = await fetchWithAuth('/api/v1/super-admin/businesses/' + deleteBusiness.id, { method: 'DELETE', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ confirm_name: businessConfirmation }) });
      if (!response.ok) throw new Error(await apiError(response, 'Business could not be deleted.'));
      flash(deleteBusiness.name + ' and its tenant data were permanently deleted.');
      setDeleteBusiness(null); setBusinessConfirmation(''); await loadData(analyticsDays);
    } catch (deleteError) { setError(deleteError instanceof Error ? deleteError.message : 'Business could not be deleted.'); } finally { setSaving(false); }
  }

  const tabs: { id: Tab; label: string }[] = [
    { id: 'overview', label: 'Overview' },
    { id: 'businesses', label: 'Businesses' },
    { id: 'users', label: 'Users & access' },
    { id: 'analytics', label: 'Analytics' },
    { id: 'system', label: 'System health' },
  ];

  return (
    <div className='min-h-full bg-background text-foreground'>
      <main className='mx-auto max-w-[1440px] px-6 py-8 sm:px-10 lg:px-14'>
        <header className='mb-8 flex flex-wrap items-end justify-between gap-5'>
          <div><h1 className='text-3xl font-black tracking-tight sm:text-4xl'>Super Admin Dashboard</h1></div>
          <button type='button' onClick={() => void loadData(analyticsDays)} disabled={loading || saving} className='ds-button ds-button-secondary'><RefreshCw size={15} className={loading ? 'animate-spin' : ''} />Refresh data</button>
        </header>
        <nav className='mb-7 flex gap-1 overflow-x-auto border-b border-border' aria-label='Super Admin sections'>{tabs.map(({ id, label }) => <button key={id} type='button' onClick={() => { setTab(id); setQuery(''); }} className={'-mb-px shrink-0 border-b-2 px-4 py-3 text-sm font-bold transition-colors ' + (tab === id ? 'border-accent text-foreground' : 'border-transparent text-muted-foreground hover:text-foreground')}>{label}</button>)}</nav>
        {notice && <div role='status' className='mb-5 rounded-xl border border-[var(--success-border)] bg-[var(--success-surface)] px-4 py-3 text-sm font-medium text-[var(--success-foreground)]'>{notice}</div>}
        {error && <div role='alert' className='mb-5 rounded-xl border border-[var(--error-border)] bg-[var(--error-surface)] px-4 py-3 text-sm font-medium text-[var(--error-foreground)]'>{error}</div>}
        {loading && !dashboard && <div className='py-24 text-center text-sm text-muted-foreground'>Loading live platform data…</div>}

        {dashboard && tab === 'overview' && <Overview dashboard={dashboard} onBusinesses={() => setTab('businesses')} onUsers={() => setTab('users')} />}

        {tab === 'businesses' && <section>
          <div className='mb-5 flex flex-wrap items-end justify-between gap-3'><div><h2 className='text-xl font-black'>Businesses</h2><p className='mt-1 text-sm text-muted-foreground'>Create, manage, archive, or permanently delete a tenant.</p></div><button type='button' onClick={() => { closeBusinessForm(); setShowBusinessForm(true); }} className='ds-button ds-button-primary'><Plus size={16} />Create business</button></div>
          {showBusinessForm && <BusinessEditor form={businessForm} setForm={setBusinessForm} editing={Boolean(editingBusiness)} saving={saving} onCancel={closeBusinessForm} onSubmit={saveBusiness} />}
          <div className='ds-card overflow-hidden'><SearchBox value={query} onChange={setQuery} placeholder='Search businesses or owners…' /><div className='overflow-x-auto'><table className='w-full min-w-[820px] text-left text-sm'><thead className='bg-surface-wash text-[11px] font-black uppercase tracking-wider text-muted-foreground'><tr><th className='p-4'>Business</th><th className='p-4'>Owner</th><th className='p-4'>Status</th><th className='p-4'>Users</th><th className='p-4'>Messages</th><th className='p-4 text-right'>Actions</th></tr></thead><tbody className='divide-y divide-border'>{matchingBusinesses.map((item) => <tr key={item.id} className='hover:bg-surface-wash/50'><td className='p-4'><p className='font-bold'>{item.name}</p><p className='mt-0.5 text-xs text-muted-foreground'>Created {dateLabel(item.created_at)}</p></td><td className='p-4 text-muted-foreground'>{item.owner_email || 'Awaiting owner invitation'}</td><td className='p-4'><StatusBadge active={item.is_active} /></td><td className='p-4 font-semibold'>{item.user_count}</td><td className='p-4 font-semibold'>{item.message_count.toLocaleString()}</td><td className='p-4'><div className='flex justify-end gap-3'><button type='button' onClick={() => editBusiness(item)} className='text-button'>Edit</button><button type='button' onClick={() => { setInviteBusiness(item); setInviteEmail(''); }} className='text-button'>Invite owner</button><button type='button' onClick={() => void changeBusinessStatus(item)} className='text-button'>{item.is_active ? 'Archive' : 'Reactivate'}</button><button type='button' onClick={() => { setDeleteBusiness(item); setBusinessConfirmation(''); }} className='text-button text-[var(--error-foreground)]'>Delete</button></div></td></tr>)}{!matchingBusinesses.length && <EmptyRow columns={6} message='No businesses match this search.' />}</tbody></table></div></div>
        </section>}

        {tab === 'users' && <section>
          <div className='mb-5 flex flex-wrap items-end justify-between gap-3'><div><h2 className='text-xl font-black'>Users & access</h2><p className='mt-1 text-sm text-muted-foreground'>Invite a business admin, supervisor, or agent without sharing social-media credentials.</p></div><div className='flex flex-wrap gap-2'><button type='button' onClick={() => { setShowTeamInvitation(true); setTeamInvitationBusinessId(''); setTeamInvitationEmail(''); setTeamInvitationRole('agent'); }} className='ds-button ds-button-secondary'>Invite team member</button><button type='button' onClick={() => { closeUserForm(); setShowUserForm(true); }} className='ds-button ds-button-primary'><Plus size={16} />Create user</button></div></div>
          {showUserForm && <UserEditor form={userForm} setForm={setUserForm} businesses={businesses} editing={Boolean(editingUser)} saving={saving} onCancel={closeUserForm} onSubmit={saveUser} />}
          <div className='ds-card overflow-hidden'><SearchBox value={query} onChange={setQuery} placeholder='Search people, email, or business…' /><div className='overflow-x-auto'><table className='w-full min-w-[820px] text-left text-sm'><thead className='bg-surface-wash text-[11px] font-black uppercase tracking-wider text-muted-foreground'><tr><th className='p-4'>Person</th><th className='p-4'>Business</th><th className='p-4'>Role</th><th className='p-4'>Status</th><th className='p-4'>Joined</th><th className='p-4 text-right'>Actions</th></tr></thead><tbody className='divide-y divide-border'>{matchingUsers.map((item) => <tr key={item.id} className='hover:bg-surface-wash/50'><td className='p-4'><p className='font-bold'>{item.name}</p><p className='mt-0.5 text-xs text-muted-foreground'>{item.email}</p></td><td className='p-4 text-muted-foreground'>{item.business_name || 'Platform account'}</td><td className='p-4'><RoleBadge role={item.role} /></td><td className='p-4 capitalize text-muted-foreground'>{item.status || 'offline'}</td><td className='p-4 text-muted-foreground'>{dateLabel(item.created_at)}</td><td className='p-4'><div className='flex justify-end gap-2'>{item.role !== 'super_admin' && <><button type='button' onClick={() => editUser(item)} className='icon-button' aria-label={'Edit ' + item.name}><UserCog size={15} /></button><button type='button' onClick={() => { setDeleteUser(item); setConfirmation(''); }} className='icon-button text-[var(--error-foreground)]' aria-label={'Delete ' + item.name}><Trash2 size={15} /></button></>}</div></td></tr>)}{!matchingUsers.length && <EmptyRow columns={6} message='No users match this search.' />}</tbody></table></div></div>
        </section>}

        {analytics && tab === 'analytics' && <AnalyticsPanel analytics={analytics} days={analyticsDays} onDaysChange={setAnalyticsDays} />}
        {dashboard && tab === 'system' && <SystemPanel dashboard={dashboard} />}
      </main>
      {inviteBusiness && <Modal title={'Invite an owner to ' + inviteBusiness.name} onClose={() => setInviteBusiness(null)}><form onSubmit={sendOwnerInvite} className='space-y-4'><p className='text-sm text-muted-foreground'>The owner completes registration from a secure link. Connected channel credentials remain private.</p><label className='block text-sm font-bold'>Owner email<input required type='email' value={inviteEmail} onChange={(event) => setInviteEmail(event.target.value)} className='ds-input mt-1.5' placeholder='owner@business.com' /></label><ModalActions saving={saving} label='Send invitation' onCancel={() => setInviteBusiness(null)} /></form></Modal>}
      {showTeamInvitation && <Modal title='Invite a team member' onClose={() => setShowTeamInvitation(false)}><form onSubmit={sendTeamInvitation} className='space-y-4'><p className='text-sm text-muted-foreground'>The invitee creates their own password. No social-media credentials are shared.</p><label className='block text-sm font-bold'>Business<select required value={teamInvitationBusinessId} onChange={(event) => setTeamInvitationBusinessId(event.target.value)} className='ds-input mt-1.5'><option value=''>Select a business</option>{businesses.filter((item) => item.is_active).map((item) => <option key={item.id} value={item.id}>{item.name}</option>)}</select></label><label className='block text-sm font-bold'>Email<input required type='email' value={teamInvitationEmail} onChange={(event) => setTeamInvitationEmail(event.target.value)} className='ds-input mt-1.5' placeholder='teammate@business.com' /></label><label className='block text-sm font-bold'>Role<select value={teamInvitationRole} onChange={(event) => setTeamInvitationRole(event.target.value)} className='ds-input mt-1.5'><option value='business_admin'>Business admin</option><option value='supervisor'>Supervisor</option><option value='agent'>Agent</option></select></label><ModalActions saving={saving} label='Send invitation' onCancel={() => setShowTeamInvitation(false)} /></form></Modal>}
      {deleteUser && <Modal title={'Permanently delete ' + deleteUser.name} onClose={() => setDeleteUser(null)}><form onSubmit={removeUser} className='space-y-4'><p className='text-sm text-muted-foreground'>This removes the login account. Customer conversations remain, but no longer identify this user.</p><label className='block text-sm font-bold'>Type {deleteUser.email} to confirm<input required type='email' value={confirmation} onChange={(event) => setConfirmation(event.target.value)} className='ds-input mt-1.5' /></label><ModalActions saving={saving} label='Permanently delete user' destructive onCancel={() => setDeleteUser(null)} /></form></Modal>}
      {deleteBusiness && <Modal title={'Permanently delete ' + deleteBusiness.name} onClose={() => setDeleteBusiness(null)}><form onSubmit={removeBusiness} className='space-y-4'><p className='text-sm text-muted-foreground'>This permanently deletes the business, its users, invitations, conversations, integrations, knowledge documents, stored files, and AI vectors. This cannot be undone.</p><label className='block text-sm font-bold'>Type {deleteBusiness.name} to confirm<input required value={businessConfirmation} onChange={(event) => setBusinessConfirmation(event.target.value)} className='ds-input mt-1.5' /></label><ModalActions saving={saving} label='Permanently delete business' destructive onCancel={() => setDeleteBusiness(null)} /></form></Modal>}
    </div>
  );
}

function Overview({ dashboard, onBusinesses, onUsers }: { dashboard: Dashboard; onBusinesses: () => void; onUsers: () => void }) {
  return <>
    <section className='grid grid-cols-2 gap-4 lg:grid-cols-3'>{dashboard.stats.map((stat) => {
      return <article key={stat.key} className='ds-card p-5 sm:p-6'><p className='text-2xl font-black tracking-tight sm:text-3xl'>{stat.value.toLocaleString()}</p><p className='mt-2 text-sm font-bold'>{stat.label}</p><p className='mt-1 text-xs text-muted-foreground'>{stat.change}</p></article>;
    })}</section>
    <section className='mt-6 grid gap-6 xl:grid-cols-[1.25fr_0.75fr]'>
      <div className='ds-card overflow-hidden'><div className='flex items-center justify-between border-b border-border p-5'><div><h2 className='font-black'>Tenant performance</h2><p className='mt-1 text-sm text-muted-foreground'>The businesses with the highest support activity.</p></div><button type='button' onClick={onBusinesses} className='text-button'>Manage businesses</button></div><div className='divide-y divide-border'>{dashboard.businesses.slice(0, 5).map((item) => <div key={item.id} className='flex items-center gap-4 p-4'><div className='min-w-0 flex-1'><p className='truncate font-bold'>{item.name}</p><p className='mt-0.5 truncate text-xs text-muted-foreground'>{item.owner}</p></div><div className='text-right'><p className='font-black'>{item.messages.toLocaleString()}</p><p className='text-xs text-muted-foreground'>messages</p></div></div>)}{!dashboard.businesses.length && <p className='p-8 text-center text-sm text-muted-foreground'>Create your first business to begin.</p>}</div></div>
      <div className='ds-card p-5'><div className='mb-4 flex items-center justify-between'><div><h2 className='font-black'>Recent activity</h2><p className='mt-1 text-sm text-muted-foreground'>Latest platform events.</p></div><button type='button' onClick={onUsers} className='text-button'>Manage users</button></div><div className='divide-y divide-border'>{dashboard.recent_activity.slice(0, 5).map((item, index) => <div key={item.action + index} className='flex gap-3 py-3'><span className='mt-1.5 h-2 w-2 shrink-0 rounded-full bg-accent' /><div className='min-w-0 flex-1'><p className='truncate text-sm font-semibold'>{item.action}</p><p className='truncate text-xs text-muted-foreground'>{item.target}</p></div><time className='shrink-0 text-[11px] text-muted-foreground'>{timeAgo(item.timestamp)}</time></div>)}</div></div>
    </section>
  </>;
}

function BusinessEditor({ form, setForm, editing, saving, onCancel, onSubmit }: { form: BusinessForm; setForm: (value: BusinessForm) => void; editing: boolean; saving: boolean; onCancel: () => void; onSubmit: (event: React.FormEvent<HTMLFormElement>) => void }) {
  const change = (key: keyof BusinessForm, value: string) => setForm({ ...form, [key]: value });
  return <form onSubmit={onSubmit} className='ds-card mb-5 p-5 sm:p-6'><div className='mb-5 flex items-start justify-between gap-4'><div><h3 className='font-black'>{editing ? 'Edit business' : 'Create a business'}</h3><p className='mt-1 text-sm text-muted-foreground'>{editing ? 'Update the tenant profile and its platform details.' : 'Create the tenant, then send its business owner a registration invitation.'}</p></div><button type='button' className='icon-button' onClick={onCancel} aria-label='Close business form'><X size={16} /></button></div><div className='grid gap-4 md:grid-cols-2'><InputField label='Business name' value={form.name} onChange={(value) => change('name', value)} placeholder='Acme Retail' required /><InputField label='Business email' value={form.email} onChange={(value) => change('email', value)} placeholder='hello@acme.com' type='email' /><InputField label='Phone' value={form.phone} onChange={(value) => change('phone', value)} placeholder='+977 …' /><InputField label='Website' value={form.website} onChange={(value) => change('website', value)} placeholder='https://acme.com' type='url' />{!editing && <InputField label='Business owner email' value={form.owner_email} onChange={(value) => change('owner_email', value)} placeholder='owner@acme.com' type='email' hint='Optional. A secure business-admin registration invitation is created.' />}</div><label className='mt-4 block text-sm font-bold'>Description<textarea value={form.description} onChange={(event) => change('description', event.target.value)} className='ds-input mt-1.5 min-h-24 resize-y' placeholder='What does this business do?' /></label><EditorActions saving={saving} label={editing ? 'Save changes' : 'Create business'} onCancel={onCancel} /></form>;
}

function UserEditor({ form, setForm, businesses, editing, saving, onCancel, onSubmit }: { form: UserForm; setForm: (value: UserForm) => void; businesses: Business[]; editing: boolean; saving: boolean; onCancel: () => void; onSubmit: (event: React.FormEvent<HTMLFormElement>) => void }) {
  const change = (key: keyof UserForm, value: string) => setForm({ ...form, [key]: value });
  return <form onSubmit={onSubmit} className='ds-card mb-5 p-5 sm:p-6'><div className='mb-5 flex items-start justify-between gap-4'><div><h3 className='font-black'>{editing ? 'Edit user access' : 'Create a user'}</h3><p className='mt-1 text-sm text-muted-foreground'>Every user belongs to one business. Their access never includes connected social-media credentials.</p></div><button type='button' className='icon-button' onClick={onCancel} aria-label='Close user form'><X size={16} /></button></div><div className='grid gap-4 md:grid-cols-2'><InputField label='Full name' value={form.name} onChange={(value) => change('name', value)} placeholder='Support Agent' required /><InputField label='Email' value={form.email} onChange={(value) => change('email', value)} placeholder='agent@business.com' required type='email' />{!editing && <InputField label='Temporary password' value={form.password} onChange={(value) => change('password', value)} placeholder='At least 8 characters' required type='password' />}</div><div className='mt-4 grid gap-4 md:grid-cols-2'><label className='block text-sm font-bold'>Business<select required value={form.business_id} onChange={(event) => change('business_id', event.target.value)} className='ds-input mt-1.5'><option value=''>Select a business</option>{businesses.filter((item) => item.is_active).map((item) => <option key={item.id} value={item.id}>{item.name}</option>)}</select></label><label className='block text-sm font-bold'>Role<select value={form.role} onChange={(event) => change('role', event.target.value)} className='ds-input mt-1.5'><option value='agent'>Agent</option><option value='supervisor'>Supervisor</option><option value='business_admin'>Business admin</option></select></label></div><EditorActions saving={saving} label={editing ? 'Save access' : 'Create user'} onCancel={onCancel} /></form>;
}

function AnalyticsPanel({ analytics, days, onDaysChange }: { analytics: Analytics; days: number; onDaysChange: (days: number) => void }) {
  const maxMessages = Math.max(...analytics.channels.map((item) => item.messages), 1);
  return <section><div className='mb-5 flex flex-wrap items-end justify-between gap-3'><div><h2 className='text-xl font-black'>Platform analytics</h2><p className='mt-1 text-sm text-muted-foreground'>Use support activity to identify where businesses need attention. Revenue is not inferred from support data.</p></div><label className='text-sm font-bold'>Period<select value={days} onChange={(event) => onDaysChange(Number(event.target.value))} className='ds-input ml-2 inline-block w-auto'><option value={7}>Last 7 days</option><option value={30}>Last 30 days</option><option value={90}>Last 90 days</option><option value={365}>Last year</option></select></label></div><div className='mb-6 grid grid-cols-2 gap-4 lg:grid-cols-4'><Metric label='Messages received' value={analytics.totals.messages_in_period} /><Metric label='New conversations' value={analytics.totals.conversations_in_period} /><Metric label='Customers' value={analytics.totals.customers} /><Metric label='Knowledge documents' value={analytics.totals.knowledge_documents} /></div><div className='grid gap-6 xl:grid-cols-[0.8fr_1.2fr]'><section className='ds-card p-5 sm:p-6'><h3 className='font-black'>Channel demand</h3><p className='mt-1 text-sm text-muted-foreground'>Channels creating the most support work.</p><div className='mt-6 space-y-5'>{analytics.channels.map((item) => <div key={item.platform}><div className='mb-2 flex justify-between text-sm'><span className='capitalize font-bold'>{item.platform.replace('_', ' ')}</span><span className='text-muted-foreground'>{item.messages.toLocaleString()}</span></div><div className='h-2 overflow-hidden rounded-full bg-surface-wash'><div className='h-full rounded-full bg-accent' style={{ width: Math.max((item.messages / maxMessages) * 100, 2) + '%' }} /></div></div>)}{!analytics.channels.length && <p className='py-8 text-center text-sm text-muted-foreground'>No channel activity in this period.</p>}</div></section><section className='ds-card overflow-hidden'><div className='border-b border-border p-5 sm:p-6'><h3 className='font-black'>Business comparison</h3><p className='mt-1 text-sm text-muted-foreground'>Compare workload, customer volume, integrations, and AI use.</p></div><div className='overflow-x-auto'><table className='w-full min-w-[670px] text-left text-sm'><thead className='bg-surface-wash text-[11px] font-black uppercase tracking-wider text-muted-foreground'><tr><th className='p-4'>Business</th><th className='p-4'>Messages</th><th className='p-4'>Customers</th><th className='p-4'>AI drafts</th><th className='p-4'>Integrations</th></tr></thead><tbody className='divide-y divide-border'>{analytics.businesses.slice(0, 10).map((item) => <tr key={item.id}><td className='p-4 font-bold'>{item.name}</td><td className='p-4'>{item.messages.toLocaleString()}</td><td className='p-4'>{item.customers.toLocaleString()}</td><td className='p-4'>{item.ai_drafts.toLocaleString()}</td><td className='p-4'>{item.integrations}</td></tr>)}{!analytics.businesses.length && <EmptyRow columns={5} message='No tenant activity yet.' />}</tbody></table></div></section></div><p className='mt-4 text-xs text-muted-foreground'>{analytics.data_note}</p></section>;
}

function SystemPanel({ dashboard }: { dashboard: Dashboard }) {
  return <section><div className='mb-5'><h2 className='text-xl font-black'>System health</h2><p className='mt-1 text-sm text-muted-foreground'>At-a-glance runtime checks and platform data volume.</p></div><div className='grid gap-6 lg:grid-cols-2'><section className='ds-card p-5 sm:p-6'><div className='mb-5'><h3 className='font-black'>Service status</h3></div><div className='space-y-3'>{dashboard.system_health.map((item) => <div key={item.label} className='flex items-center justify-between rounded-xl bg-surface-wash p-4'><div><p className='font-bold'>{item.label}</p><p className='mt-1 text-xs text-muted-foreground'>{item.detail}</p></div><span className='flex items-center gap-1.5 text-xs font-bold text-[var(--success-foreground)]'><span className='h-2 w-2 rounded-full bg-[var(--success)]' />{item.status}</span></div>)}</div></section><section className='ds-card p-5 sm:p-6'><div className='mb-5'><h3 className='font-black'>Data volume</h3></div><dl className='divide-y divide-border'>{dashboard.database_stats.map((item) => <div key={item.label} className='flex items-center justify-between py-3'><dt className='text-sm text-muted-foreground'>{item.label}</dt><dd className='text-lg font-black'>{item.value.toLocaleString()}</dd></div>)}</dl></section></div></section>;
}

function Metric({ label, value }: { label: string; value: number }) { return <article className='ds-card p-5'><p className='text-2xl font-black'>{value.toLocaleString()}</p><p className='mt-2 text-sm font-bold'>{label}</p></article>; }
function StatusBadge({ active }: { active: boolean }) { return <span className={'rounded-full px-2.5 py-1 text-xs font-bold ' + (active ? 'bg-[var(--success-surface)] text-[var(--success-foreground)]' : 'bg-surface-wash text-muted-foreground')}>{active ? 'Active' : 'Archived'}</span>; }
function RoleBadge({ role }: { role: string }) { return <span className='rounded-full bg-surface-wash px-2.5 py-1 text-xs font-bold capitalize'>{role.replace('_', ' ')}</span>; }
function EmptyRow({ columns, message }: { columns: number; message: string }) { return <tr><td colSpan={columns} className='p-10 text-center text-muted-foreground'>{message}</td></tr>; }
function SearchBox({ value, onChange, placeholder }: { value: string; onChange: (value: string) => void; placeholder: string }) { return <label className='relative block border-b border-border p-4'><span className='sr-only'>Search</span><Search size={15} className='absolute left-7 top-7 text-muted-foreground' /><input value={value} onChange={(event) => onChange(event.target.value)} className='ds-input pl-9' placeholder={placeholder} /></label>; }
function InputField({ label, value, onChange, placeholder, type = 'text', required = false, hint }: { label: string; value: string; onChange: (value: string) => void; placeholder: string; type?: string; required?: boolean; hint?: string }) { return <label className='block text-sm font-bold'>{label}<input required={required} type={type} value={value} onChange={(event) => onChange(event.target.value)} className='ds-input mt-1.5' placeholder={placeholder} />{hint && <span className='mt-1 block text-xs font-normal text-muted-foreground'>{hint}</span>}</label>; }
function EditorActions({ saving, label, onCancel }: { saving: boolean; label: string; onCancel: () => void }) { return <div className='mt-5 flex justify-end gap-3'><button type='button' onClick={onCancel} className='ds-button ds-button-secondary'>Cancel</button><button disabled={saving} className='ds-button ds-button-primary'>{saving ? 'Saving…' : label}</button></div>; }
function Modal({ title, onClose, children }: { title: string; onClose: () => void; children: ReactNode }) { return <div className='fixed inset-0 z-[100] flex items-center justify-center bg-slate-950/20 p-4 backdrop-blur-sm' role='presentation'><div role='dialog' aria-modal='true' aria-label={title} className='w-full max-w-lg rounded-2xl border border-border bg-background p-6 shadow-2xl'><div className='mb-5 flex items-start justify-between gap-4'><h2 className='text-xl font-black'>{title}</h2><button type='button' className='icon-button' onClick={onClose} aria-label='Close dialog'><X size={16} /></button></div>{children}</div></div>; }
function ModalActions({ saving, label, destructive = false, onCancel }: { saving: boolean; label: string; destructive?: boolean; onCancel: () => void }) { return <div className='flex justify-end gap-3'><button type='button' onClick={onCancel} className='ds-button ds-button-secondary'>Cancel</button><button disabled={saving} className={destructive ? 'ds-button bg-[var(--error)] text-white hover:opacity-90' : 'ds-button ds-button-primary'}>{saving ? 'Working…' : label}</button></div>; }
