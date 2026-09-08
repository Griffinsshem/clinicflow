"use client";

import { useState } from "react";

import { Button } from "./Button";
import { Modal } from "./Modal";

export function ConfirmDialog({
  open,
  title,
  description,
  confirmLabel,
  onConfirm,
  onCancel,
}: {
  open: boolean;
  title: string;
  description: string;
  confirmLabel: string;
  onConfirm: () => Promise<void>;
  onCancel: () => void;
}) {
  const [working, setWorking] = useState(false);

  async function confirm() {
    setWorking(true);
    try {
      await onConfirm();
    } finally {
      setWorking(false);
    }
  }

  return (
    <Modal open={open} onClose={onCancel} title={title}>
      <p className="text-ink-muted">{description}</p>
      <div className="mt-5 flex justify-end gap-2">
        <Button onClick={onCancel} disabled={working}>
          Cancel
        </Button>
        <Button variant="danger" onClick={confirm} loading={working}>
          {confirmLabel}
        </Button>
      </div>
    </Modal>
  );
}
