"use client";

import React, { useState, useEffect } from "react";
import {
  Users,
  UserPlus,
  Shield,
  Trash2,
  CheckCircle2,
  AlertCircle,
  Loader2,
  Lock,
  Mail,
} from "lucide-react";
import { Navbar } from "@/components/Navbar";
import { useAuth } from "@/lib/auth";
import { api, Membership } from "@/lib/api";
import { formatDate } from "@/lib/utils";
import { StatusBadge } from "@/components/StatusBadge";

export default function MembersPage() {
  const { currentBusiness } = useAuth();
  const [members, setMembers] = useState<Membership[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  // Invite Form State
  const [inviteEmail, setInviteEmail] = useState("");
  const [inviteRole, setInviteRole] = useState<"OWNER" | "FINANCE_MANAGER" | "ACCOUNTANT" | "VIEWER">("ACCOUNTANT");
  const [isInviting, setIsInviting] = useState(false);

  const isOwner = currentBusiness?.role === "OWNER";

  useEffect(() => {
    loadMembers();
  }, [currentBusiness]);

  async function loadMembers() {
    if (!currentBusiness) return;
    setLoading(true);
    setError(null);
    try {
      const data = await api.listMembers(currentBusiness.id);
      setMembers(data);
    } catch (err: any) {
      setError(err.message || "Failed to load team members.");
    } finally {
      setLoading(false);
    }
  }

  const handleInvite = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!currentBusiness || !isOwner || !inviteEmail.trim()) return;

    setError(null);
    setSuccess(null);
    setIsInviting(true);

    try {
      await api.inviteMember(currentBusiness.id, inviteEmail, inviteRole);
      setSuccess(`Member '${inviteEmail}' successfully added with role ${inviteRole}.`);
      setInviteEmail("");
      await loadMembers();
      setTimeout(() => setSuccess(null), 4000);
    } catch (err: any) {
      setError(err.message || "Failed to add team member.");
    } finally {
      setIsInviting(false);
    }
  };

  const handleUpdateRole = async (memberId: string, newRole: string) => {
    if (!currentBusiness || !isOwner) return;
    setError(null);
    try {
      await api.updateMemberRole(currentBusiness.id, memberId, newRole);
      await loadMembers();
    } catch (err: any) {
      setError(err.message || "Failed to update member role.");
    }
  };

  const handleRemoveMember = async (memberId: string, email: string) => {
    if (!currentBusiness || !isOwner) return;
    if (!confirm(`Are you sure you want to remove ${email} from ${currentBusiness.name}?`)) {
      return;
    }
    setError(null);
    try {
      await api.removeMember(currentBusiness.id, memberId);
      await loadMembers();
    } catch (err: any) {
      setError(err.message || "Failed to remove member.");
    }
  };

  return (
    <div>
      <Navbar
        title="Team Members & Role-Based Permissions"
        subtitle="Control access levels across your organization (OWNER, FINANCE_MANAGER, ACCOUNTANT, VIEWER)"
      />

      <div className="mt-6 max-w-5xl mx-auto space-y-8">
        {error && (
          <div className="p-4 rounded-xl bg-rose-50 border border-rose-200 text-rose-700 text-sm flex items-start gap-3">
            <AlertCircle className="w-5 h-5 shrink-0 mt-0.5" />
            <span>{error}</span>
          </div>
        )}

        {success && (
          <div className="p-4 rounded-xl bg-emerald-50 border border-emerald-200 text-emerald-800 text-sm flex items-center gap-2">
            <CheckCircle2 className="w-4 h-4 text-[#10A86B]" />
            <span>{success}</span>
          </div>
        )}

        {/* Add Member Card (Only OWNER can invite) */}
        {isOwner ? (
          <div className="bg-white rounded-2xl border border-slate-200/80 shadow-sm p-6 sm:p-8">
            <div className="flex items-center gap-3 pb-4 border-b border-slate-100 mb-6">
              <div className="w-10 h-10 rounded-xl bg-[#E8F8F1] text-[#10A86B] flex items-center justify-center">
                <UserPlus className="w-5 h-5" />
              </div>
              <div>
                <h3 className="font-bold text-slate-900 text-base">Add or Invite Team Member</h3>
                <p className="text-xs text-slate-500">Grant authorized access to this business workspace</p>
              </div>
            </div>

            <form onSubmit={handleInvite} className="grid grid-cols-1 sm:grid-cols-12 gap-4 items-end">
              <div className="sm:col-span-6">
                <label className="block text-xs font-semibold uppercase tracking-wider text-slate-700 mb-1.5">
                  User Email Address
                </label>
                <div className="relative">
                  <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-slate-400">
                    <Mail className="w-4 h-4" />
                  </div>
                  <input
                    type="email"
                    required
                    value={inviteEmail}
                    onChange={(e) => setInviteEmail(e.target.value)}
                    placeholder="colleague@company.com"
                    className="block w-full pl-9 pr-3 py-2.5 bg-slate-50 border border-slate-300 rounded-xl text-slate-900 text-xs focus:outline-none focus:ring-2 focus:ring-[#10A86B]"
                  />
                </div>
              </div>

              <div className="sm:col-span-4">
                <label className="block text-xs font-semibold uppercase tracking-wider text-slate-700 mb-1.5">
                  Role & Permissions
                </label>
                <select
                  value={inviteRole}
                  onChange={(e) => setInviteRole(e.target.value as any)}
                  className="block w-full px-3 py-2.5 bg-slate-50 border border-slate-300 rounded-xl text-slate-900 text-xs focus:outline-none focus:ring-2 focus:ring-[#10A86B]"
                >
                  <option value="OWNER">Owner (Full Management)</option>
                  <option value="FINANCE_MANAGER">Finance Manager (Approve Imports & Accounts)</option>
                  <option value="ACCOUNTANT">Accountant (Upload & Review Records)</option>
                  <option value="VIEWER">Viewer (Read-Only Access)</option>
                </select>
              </div>

              <div className="sm:col-span-2">
                <button
                  type="submit"
                  disabled={isInviting || !inviteEmail.trim()}
                  className="w-full inline-flex items-center justify-center gap-1.5 py-2.5 px-4 bg-[#10A86B] hover:bg-[#0D8554] text-white font-semibold rounded-xl text-xs shadow-sm transition-colors disabled:opacity-50"
                >
                  {isInviting ? <Loader2 className="w-4 h-4 animate-spin" /> : <UserPlus className="w-4 h-4" />}
                  <span>Invite</span>
                </button>
              </div>
            </form>
          </div>
        ) : (
          <div className="bg-amber-50 border border-amber-200 rounded-2xl p-4 text-xs text-amber-800 flex items-center gap-2">
            <Lock className="w-4 h-4 text-amber-600 shrink-0" />
            <span>
              You have {currentBusiness?.role} permissions. Only workspace <strong>OWNERS</strong> can invite members or modify roles.
            </span>
          </div>
        )}

        {/* Existing Members Table */}
        <div className="bg-white rounded-2xl border border-slate-200/80 shadow-sm overflow-hidden">
          <div className="p-5 border-b border-slate-200/80">
            <h3 className="font-bold text-slate-900 text-base">Active Team Members</h3>
            <p className="text-xs text-slate-500">
              {members.length} member(s) have authorized access to {currentBusiness?.name}
            </p>
          </div>

          {loading ? (
            <div className="p-12 text-center">
              <Loader2 className="w-6 h-6 text-[#10A86B] animate-spin mx-auto mb-2" />
              <p className="text-xs text-slate-500">Loading memberships...</p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs text-slate-600">
                <thead className="bg-slate-50 text-[10px] font-bold text-slate-500 uppercase tracking-wider border-b border-slate-200">
                  <tr>
                    <th className="py-3 px-5">Member</th>
                    <th className="py-3 px-5">Email Address</th>
                    <th className="py-3 px-5">Assigned Role</th>
                    <th className="py-3 px-5">Added On</th>
                    {isOwner && <th className="py-3 px-5 text-right">Actions</th>}
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {members.map((m) => (
                    <tr key={m.id} className="hover:bg-slate-50/70 transition-colors">
                      <td className="py-3.5 px-5 font-bold text-slate-900">
                        {m.user?.full_name || "Team Member"}
                      </td>
                      <td className="py-3.5 px-5 text-slate-500 font-mono">
                        {m.user?.email}
                      </td>
                      <td className="py-3.5 px-5 whitespace-nowrap">
                        {isOwner ? (
                          <select
                            value={m.role}
                            onChange={(e) => handleUpdateRole(m.id, e.target.value)}
                            className="px-2 py-1 bg-slate-50 border border-slate-200 rounded-lg text-xs font-semibold text-slate-700 focus:outline-none focus:ring-1 focus:ring-[#10A86B]"
                          >
                            <option value="OWNER">Owner</option>
                            <option value="FINANCE_MANAGER">Finance Manager</option>
                            <option value="ACCOUNTANT">Accountant</option>
                            <option value="VIEWER">Viewer</option>
                          </select>
                        ) : (
                          <StatusBadge status={m.role} type="role" />
                        )}
                      </td>
                      <td className="py-3.5 px-5 text-slate-400 whitespace-nowrap">
                        {formatDate(m.created_at)}
                      </td>
                      {isOwner && (
                        <td className="py-3.5 px-5 text-right whitespace-nowrap">
                          <button
                            onClick={() => handleRemoveMember(m.id, m.user.email)}
                            title="Remove Member"
                            className="p-1.5 text-slate-400 hover:text-rose-600 hover:bg-rose-50 rounded-lg transition-colors"
                          >
                            <Trash2 className="w-4 h-4" />
                          </button>
                        </td>
                      )}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>

        {/* Roles & Permissions Reference Card */}
        <div className="bg-slate-50 rounded-2xl border border-slate-200/80 p-6">
          <h4 className="text-xs font-bold uppercase tracking-wider text-slate-700 mb-3 flex items-center gap-1.5">
            <Shield className="w-4 h-4 text-[#10A86B]" />
            Role Permissions Overview
          </h4>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 text-xs">
            <div className="p-3 bg-white rounded-xl border border-slate-200">
              <p className="font-bold text-indigo-700 mb-1">OWNER</p>
              <p className="text-slate-500">
                Full authority. Can manage business settings, invite members, modify roles, and approve imports.
              </p>
            </div>
            <div className="p-3 bg-white rounded-xl border border-slate-200">
              <p className="font-bold text-blue-700 mb-1">FINANCE MANAGER</p>
              <p className="text-slate-500">
                Can create accounts, upload files, and review & confirm financial imports into the ledger.
              </p>
            </div>
            <div className="p-3 bg-white rounded-xl border border-slate-200">
              <p className="font-bold text-emerald-700 mb-1">ACCOUNTANT</p>
              <p className="text-slate-500">
                Can upload files, inspect column mappings, and preview validation results. Cannot confirm imports.
              </p>
            </div>
            <div className="p-3 bg-white rounded-xl border border-slate-200">
              <p className="font-bold text-slate-700 mb-1">VIEWER</p>
              <p className="text-slate-500">
                Read-only access to authorized records, accounts, and reports. Cannot modify or upload data.
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
