// frontend/src/features/settings/components/QuietComponentsDemo.tsx

import { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { QuietInput, QuietTextarea } from '@/components/ui/quiet-input';
import {
  QuietSelect,
  QuietSelectContent,
  QuietSelectItem,
  QuietSelectTrigger,
  QuietSelectValue,
} from '@/components/ui/quiet-select';
import { QuietDateInput } from '@/components/ui/quiet-date';
import {
  QuietChipLabel,
  QuietChipSelectable,
  QuietChipStatus,
  QuietChipTag,
} from '@/components/ui/quiet-chip';

export function QuietComponentsDemo() {
  const { t } = useTranslation();
  const [name, setName] = useState('');
  const [notes, setNotes] = useState('');
  const [role, setRole] = useState('member');
  const [dueDate, setDueDate] = useState<Date | undefined>();
  const [tagVisible, setTagVisible] = useState(true);
  const [selectedFilter, setSelectedFilter] = useState(false);

  return (
    <section className="space-y-6">
      <div>
        <h2 className="text-lg font-medium text-[color:var(--app-text-strong)]">
          {t('settings.quietDemo.title')}
        </h2>
        <p className="mt-1 text-sm text-[color:var(--app-text-muted)]">
          {t('settings.quietDemo.description')}
        </p>
      </div>

      <div className="grid gap-4 md:grid-cols-2">
        <label className="block space-y-2">
          <span className="text-sm font-medium text-[color:var(--app-text)]">
            {t('settings.quietDemo.nameLabel')}
          </span>
          <QuietInput
            value={name}
            onChange={(e) => setName(e.target.value)}
            placeholder={t('settings.quietDemo.nameLabel')}
          />
        </label>

        <label className="block space-y-2">
          <span className="text-sm font-medium text-[color:var(--app-text)]">
            {t('settings.quietDemo.roleLabel')}
          </span>
          <QuietSelect value={role} onValueChange={setRole}>
            <QuietSelectTrigger fullWidth>
              <QuietSelectValue placeholder={t('common.select')} />
            </QuietSelectTrigger>
            <QuietSelectContent>
              <QuietSelectItem value="admin">{t('settings.quietDemo.roles.admin')}</QuietSelectItem>
              <QuietSelectItem value="member">{t('settings.quietDemo.roles.member')}</QuietSelectItem>
              <QuietSelectItem value="viewer">{t('settings.quietDemo.roles.viewer')}</QuietSelectItem>
            </QuietSelectContent>
          </QuietSelect>
        </label>

        <label className="block space-y-2 md:col-span-2">
          <span className="text-sm font-medium text-[color:var(--app-text)]">
            {t('settings.quietDemo.notesLabel')}
          </span>
          <QuietTextarea
            value={notes}
            onChange={(e) => setNotes(e.target.value)}
            rows={3}
          />
        </label>

        <label className="block space-y-2">
          <span className="text-sm font-medium text-[color:var(--app-text)]">
            {t('settings.quietDemo.dueDateLabel')}
          </span>
          <QuietDateInput value={dueDate} onChange={setDueDate} />
        </label>
      </div>

      <div className="space-y-3">
        <p className="text-sm font-medium text-[color:var(--app-text)]">
          {t('settings.quietDemo.chipsLabel')}
        </p>
        <div className="flex flex-wrap gap-2">
          <QuietChipStatus intent="default">{t('settings.quietDemo.status.draft')}</QuietChipStatus>
          <QuietChipStatus intent="success">{t('settings.quietDemo.status.active')}</QuietChipStatus>
          <QuietChipStatus intent="warn">{t('settings.quietDemo.status.pending')}</QuietChipStatus>
          <QuietChipStatus intent="danger">{t('settings.quietDemo.status.failed')}</QuietChipStatus>
          <QuietChipLabel>{t('settings.quietDemo.status.label')}</QuietChipLabel>
          {tagVisible && (
            <QuietChipTag onDismiss={() => setTagVisible(false)}>
              {t('settings.quietDemo.status.tag')}
            </QuietChipTag>
          )}
          <QuietChipSelectable selected={selectedFilter} onToggle={setSelectedFilter}>
            {t('settings.quietDemo.status.filter')}
          </QuietChipSelectable>
        </div>
      </div>

      <div className="rounded-xl ring-1 ring-[color:var(--app-ring)] overflow-hidden">
        <div className="grid grid-cols-[1fr_auto] gap-4 px-4 py-3 bg-[color:var(--app-table-row)]">
          <span className="text-sm text-[color:var(--app-text)]">{t('settings.quietDemo.table.rowA')}</span>
          <QuietChipStatus intent="default" placement="dataRow">
            {t('settings.quietDemo.status.draft')}
          </QuietChipStatus>
        </div>
        <div className="grid grid-cols-[1fr_auto] gap-4 px-4 py-3 bg-[color:var(--app-table-row-alt)]">
          <span className="text-sm text-[color:var(--app-text)]">{t('settings.quietDemo.table.rowB')}</span>
          <QuietChipStatus intent="success" placement="dataRow">
            {t('settings.quietDemo.status.active')}
          </QuietChipStatus>
        </div>
      </div>
    </section>
  );
}
