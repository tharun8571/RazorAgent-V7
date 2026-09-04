"use client";
import React, { useState, useEffect } from "react";
import { fetchPayments, createPaymentOrder } from "../../lib/api";
import { PaymentItem } from "../../types";
import { CreditCard, PlusCircle, ArrowUpRight, Shield, CheckCircle, AlertCircle, RefreshCw } from "lucide-react";

export default function PaymentsPage() {
  const [payments, setPayments] = useState<PaymentItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [creating, setCreating] = useState(false);
  const [result, setResult] = useState<any | null>(null);

  // Form State
  const [customerId, setCustomerId] = useState("cust_enterprise_04");
  const [amount, setAmount] = useState<number>(2499.0);
  const [currency, setCurrency] = useState("INR");
  const [method, setMethod] = useState("upi");
  const [description, setDescription] = useState("Pro Subscription Plan");

  const loadPayments = async () => {
    try {
      const data = await fetchPayments();
      setPayments(data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadPayments();
  }, []);

  const handleCreatePayment = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      setCreating(true);
      setResult(null);
      const idempotencyKey = `idem_${Date.now()}_${Math.random().toString(36).substring(2, 7)}`;
      const res = await createPaymentOrder({
        customer_id: customerId,
        amount: Number(amount),
        currency,
        method,
        idempotency_key: idempotencyKey,
        description,
      });
      setResult(res);
      await loadPayments();
    } catch (err: any) {
      alert(`Payment workflow failed: ${err.message}`);
    } finally {
      setCreating(false);
    }
  };

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-xl font-bold text-white tracking-tight">Payments Studio</h1>
        <p className="text-xs text-slate-400">
          Create test transactions and inspect LLM multi-agent execution results
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Payment Form */}
        <div className="glass-panel p-6 rounded-2xl border border-border/80 space-y-4 lg:col-span-1">
          <h2 className="text-sm font-bold text-white flex items-center space-x-2">
            <PlusCircle className="h-4 w-4 text-primary-400" />
            <span>Initiate Autonomous Payment</span>
          </h2>

          <form onSubmit={handleCreatePayment} className="space-y-4 text-xs">
            <div>
              <label className="text-slate-300 font-semibold block mb-1">Customer ID</label>
              <input
                type="text"
                value={customerId}
                onChange={(e) => setCustomerId(e.target.value)}
                required
                className="w-full bg-slate-900 border border-border rounded-xl px-3 py-2 text-white focus:outline-none focus:border-primary-500"
              />
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="text-slate-300 font-semibold block mb-1">Amount</label>
                <input
                  type="number"
                  step="0.01"
                  value={amount}
                  onChange={(e) => setAmount(Number(e.target.value))}
                  required
                  className="w-full bg-slate-900 border border-border rounded-xl px-3 py-2 text-white focus:outline-none focus:border-primary-500"
                />
              </div>
              <div>
                <label className="text-slate-300 font-semibold block mb-1">Currency</label>
                <select
                  value={currency}
                  onChange={(e) => setCurrency(e.target.value)}
                  className="w-full bg-slate-900 border border-border rounded-xl px-3 py-2 text-white focus:outline-none focus:border-primary-500"
                >
                  <option value="INR">INR (₹)</option>
                  <option value="USD">USD ($)</option>
                </select>
              </div>
            </div>

            <div>
              <label className="text-slate-300 font-semibold block mb-1">Payment Method</label>
              <select
                value={method}
                onChange={(e) => setMethod(e.target.value)}
                className="w-full bg-slate-900 border border-border rounded-xl px-3 py-2 text-white focus:outline-none focus:border-primary-500"
              >
                <option value="upi">UPI (Instant)</option>
                <option value="card">Credit / Debit Card</option>
                <option value="netbanking">NetBanking</option>
                <option value="wallet">Wallet</option>
              </select>
            </div>

            <div>
              <label className="text-slate-300 font-semibold block mb-1">Description / Notes</label>
              <input
                type="text"
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                className="w-full bg-slate-900 border border-border rounded-xl px-3 py-2 text-white focus:outline-none focus:border-primary-500"
              />
            </div>

            <button
              type="submit"
              disabled={creating}
              className="w-full py-2.5 px-4 rounded-xl bg-primary-600 hover:bg-primary-500 text-white font-semibold shadow-lg shadow-primary-600/20 transition flex items-center justify-center space-x-2 text-xs"
            >
              <CreditCard className="h-4 w-4" />
              <span>{creating ? "Running Multi-Agent Graph..." : "Execute Payment Flow"}</span>
            </button>
          </form>
        </div>

        {/* Execution Output Drawer */}
        <div className="glass-panel p-6 rounded-2xl border border-border/80 lg:col-span-2 space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-sm font-bold text-white flex items-center space-x-2">
              <Shield className="h-4 w-4 text-accent-cyan" />
              <span>Multi-Agent Workflow State &amp; Reasoning</span>
            </h2>
            {result && (
              <span className="text-xs font-mono font-bold px-2 py-0.5 rounded bg-primary-500/20 text-primary-300">
                {result.workflow_status}
              </span>
            )}
          </div>

          {result ? (
            <div className="space-y-4 text-xs">
              <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                <div className="p-3 rounded-xl bg-slate-900/80 border border-border">
                  <span className="text-[10px] text-slate-400 block">Payment ID</span>
                  <span className="font-mono font-bold text-white">{result.payment_id}</span>
                </div>
                <div className="p-3 rounded-xl bg-slate-900/80 border border-border">
                  <span className="text-[10px] text-slate-400 block">Order ID</span>
                  <span className="font-mono font-bold text-accent-cyan">{result.order_id || "—"}</span>
                </div>
                <div className="p-3 rounded-xl bg-slate-900/80 border border-border">
                  <span className="text-[10px] text-slate-400 block">Risk Score</span>
                  <span className="font-mono font-bold text-accent-emerald">
                    {result.risk_assessment?.risk_score ?? "0.0"} ({result.risk_assessment?.risk_level ?? "LOW"})
                  </span>
                </div>
                <div className="p-3 rounded-xl bg-slate-900/80 border border-border">
                  <span className="text-[10px] text-slate-400 block">HITL Required</span>
                  <span className="font-mono font-bold text-slate-200">
                    {result.requires_human_approval ? "YES" : "NO"}
                  </span>
                </div>
              </div>

              {/* Agent Reasoning Blocks */}
              <div className="space-y-2">
                <h4 className="text-[11px] font-bold text-slate-400 uppercase tracking-wider">
                  Agent Chain Decisions
                </h4>

                {result.payment_decision && (
                  <div className="p-3 rounded-xl bg-slate-950/70 border border-border">
                    <span className="text-[10px] font-bold text-indigo-400 block">[Payment Agent]</span>
                    <p className="text-slate-300 italic">{result.payment_decision.reasoning_summary}</p>
                  </div>
                )}

                {result.risk_assessment && (
                  <div className="p-3 rounded-xl bg-slate-950/70 border border-border">
                    <span className="text-[10px] font-bold text-amber-400 block">[Risk Agent]</span>
                    <p className="text-slate-300 italic">{result.risk_assessment.reasoning_summary}</p>
                  </div>
                )}

                {result.reconciliation_result && (
                  <div className="p-3 rounded-xl bg-slate-950/70 border border-border">
                    <span className="text-[10px] font-bold text-emerald-400 block">[Reconciliation Agent]</span>
                    <p className="text-slate-300 italic">{result.reconciliation_result.likely_cause}</p>
                  </div>
                )}

                {result.monitoring_decision && (
                  <div className="p-3 rounded-xl bg-slate-950/70 border border-border">
                    <span className="text-[10px] font-bold text-purple-400 block">[Monitor Agent]</span>
                    <p className="text-slate-300 italic">{result.monitoring_decision.root_cause}</p>
                  </div>
                )}
              </div>
            </div>
          ) : (
            <div className="text-center py-12 text-slate-500 text-xs">
              Execute a payment from the left panel to trace real-time multi-agent reasoning.
            </div>
          )}
        </div>
      </div>

      {/* Transaction History Table */}
      <div className="glass-panel p-6 rounded-2xl border border-border/80 space-y-4">
        <div className="flex items-center justify-between">
          <h2 className="text-sm font-bold text-white">Payment Transactions Ledger</h2>
          <button
            onClick={loadPayments}
            className="p-1.5 rounded-lg bg-slate-900 border border-border hover:bg-slate-800 text-slate-300 text-xs flex items-center space-x-1"
          >
            <RefreshCw className="h-3 w-3" />
            <span>Refresh</span>
          </button>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs font-mono">
            <thead className="border-b border-border text-slate-400 text-[10px] uppercase">
              <tr>
                <th className="py-2.5 px-3">Payment ID</th>
                <th className="py-2.5 px-3">Customer</th>
                <th className="py-2.5 px-3">Amount</th>
                <th className="py-2.5 px-3">Method</th>
                <th className="py-2.5 px-3">Status</th>
                <th className="py-2.5 px-3">Risk</th>
                <th className="py-2.5 px-3">Timestamp</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border/40 text-slate-300">
              {payments.length === 0 ? (
                <tr>
                  <td colSpan={7} className="py-6 text-center text-slate-500">
                    No transactions recorded yet.
                  </td>
                </tr>
              ) : (
                payments.map((p) => (
                  <tr key={p.payment_id} className="hover:bg-surface-hover/50 transition-colors">
                    <td className="py-3 px-3 font-bold text-white">{p.payment_id}</td>
                    <td className="py-3 px-3 text-slate-400">{p.customer_id}</td>
                    <td className="py-3 px-3 font-bold text-slate-200">
                      {p.currency} {p.amount.toFixed(2)}
                    </td>
                    <td className="py-3 px-3 uppercase text-[10px] text-slate-400">{p.method || "upi"}</td>
                    <td className="py-3 px-3">
                      <span className="px-2 py-0.5 rounded-full bg-emerald-500/10 text-accent-emerald text-[10px] font-bold">
                        {p.status}
                      </span>
                    </td>
                    <td className="py-3 px-3">
                      <span className="text-[10px] text-slate-300">
                        {p.risk_score} ({p.risk_level})
                      </span>
                    </td>
                    <td className="py-3 px-3 text-slate-400 text-[10px]">
                      {new Date(p.created_at).toLocaleTimeString()}
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
}
