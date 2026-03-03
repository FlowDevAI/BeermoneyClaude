"use client"

import { useState } from "react"
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from "@/components/ui/dialog"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import type { HumanQueueItem } from "@/lib/supabase/types"

interface CompleteTaskDialogProps {
  item: HumanQueueItem | null
  open: boolean
  onOpenChange: (open: boolean) => void
  onSave: (data: { earnings: number; currency: string; minutes: number; notes: string }) => void
}

export function CompleteTaskDialog({ item, open, onOpenChange, onSave }: CompleteTaskDialogProps) {
  const [earnings, setEarnings] = useState(item?.estimated_pay?.toString() ?? "")
  const [currency, setCurrency] = useState(item?.currency ?? "EUR")
  const [minutes, setMinutes] = useState("")
  const [notes, setNotes] = useState("")

  const earningsNum = parseFloat(earnings) || 0
  const minutesNum = parseInt(minutes) || 0
  const hourlyRate = minutesNum > 0 ? (earningsNum / minutesNum) * 60 : 0

  function handleSave() {
    onSave({
      earnings: earningsNum,
      currency,
      minutes: minutesNum,
      notes,
    })
    setEarnings("")
    setMinutes("")
    setNotes("")
  }

  if (!item) return null

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="bg-zinc-900 border-zinc-800 text-zinc-50 sm:max-w-md">
        <DialogHeader>
          <DialogTitle className="text-zinc-100">
            Complete: {item.task_title}
          </DialogTitle>
        </DialogHeader>

        <div className="flex flex-col gap-4 py-4">
          <div className="flex gap-3">
            <div className="flex-1">
              <Label htmlFor="earnings" className="text-zinc-400">How much did you earn?</Label>
              <Input
                id="earnings"
                type="number"
                step="0.01"
                placeholder="0.00"
                value={earnings}
                onChange={(e) => setEarnings(e.target.value)}
                className="mt-1.5 bg-zinc-800 border-zinc-700 text-zinc-100"
              />
            </div>
            <div className="w-24">
              <Label htmlFor="currency" className="text-zinc-400">Currency</Label>
              <select
                id="currency"
                value={currency}
                onChange={(e) => setCurrency(e.target.value)}
                className="mt-1.5 flex h-9 w-full rounded-md border border-zinc-700 bg-zinc-800 px-3 py-1 text-sm text-zinc-100"
              >
                <option value="EUR">EUR</option>
                <option value="GBP">GBP</option>
                <option value="USD">USD</option>
              </select>
            </div>
          </div>

          <div>
            <Label htmlFor="minutes" className="text-zinc-400">Time spent (minutes)</Label>
            <Input
              id="minutes"
              type="number"
              placeholder="0"
              value={minutes}
              onChange={(e) => setMinutes(e.target.value)}
              className="mt-1.5 bg-zinc-800 border-zinc-700 text-zinc-100"
            />
          </div>

          {hourlyRate > 0 && (
            <div className="rounded-lg bg-zinc-800/50 p-3 text-center">
              <span className="text-sm text-zinc-400">Effective rate: </span>
              <span className={`text-lg font-semibold ${hourlyRate >= 10 ? "text-emerald-500" : "text-amber-500"}`}>
                {hourlyRate.toFixed(2)} {currency}/h
              </span>
            </div>
          )}

          <div>
            <Label htmlFor="notes" className="text-zinc-400">Notes (optional)</Label>
            <textarea
              id="notes"
              rows={2}
              placeholder="Any notes about the task..."
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              className="mt-1.5 flex w-full rounded-md border border-zinc-700 bg-zinc-800 px-3 py-2 text-sm text-zinc-100 placeholder:text-zinc-500 focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-zinc-600"
            />
          </div>
        </div>

        <DialogFooter>
          <Button variant="ghost" onClick={() => onOpenChange(false)} className="text-zinc-400">
            Cancel
          </Button>
          <Button onClick={handleSave} className="bg-emerald-600 hover:bg-emerald-700 text-white">
            Save
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
