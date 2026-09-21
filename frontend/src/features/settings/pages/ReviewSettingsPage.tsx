// frontend/src/features/settings/pages/ReviewSettingsPage.tsx
import { useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';
import {
  QuietSelect,
  QuietSelectContent,
  QuietSelectItem,
  QuietSelectTrigger,
  QuietSelectValue,
} from '@/components/ui/quiet-select';
import { useAuth } from '@/contexts/AuthContext';
import {
  useModelCatalog,
  useModelPolicy,
  usePatchModelPolicy,
  usePatchWorkspace,
  useWorkspaceSettings,
} from '@/features/settings/hooks';
import type { ModelCatalogItem, ModelPolicyEntry, ModelPolicyRole } from '@/features/settings/types';
import { mapApiError } from '@/shared/errors';
import { notify, showDomainErrorToast } from '@/shared/errors/toasts';

const PLATFORM_DEFAULT = '__platform_default__';

const MODEL_ROLES: ModelPolicyRole[] = [
  'reviewer_standard',
  'reviewer_deep',
  'reviewer_critical',
  'judge',
];

function modelKey(entry: ModelPolicyEntry): string {
  return `${entry.provider}|${entry.model_id}`;
}

function entryFromKey(key: string): ModelPolicyEntry | null {
  if (key === PLATFORM_DEFAULT) return null;
  const separator = key.indexOf('|');
  if (separator < 0) return null;
  return {
    provider: key.slice(0, separator),
    model_id: key.slice(separator + 1),
  };
}

function selectionValue(override: ModelPolicyEntry | null | undefined): string {
  if (!override) return PLATFORM_DEFAULT;
  return modelKey(override);
}

export function ReviewSettingsPage() {
  const { t } = useTranslation();
  const { user } = useAuth();
  const workspaceId = user?.workspace_id ?? null;

  const workspaceSettings = useWorkspaceSettings(workspaceId);
  const modelPolicy = useModelPolicy(workspaceId);
  const modelCatalog = useModelCatalog(workspaceId);
  const patchWorkspace = usePatchWorkspace(workspaceId);
  const patchModelPolicy = usePatchModelPolicy(workspaceId);

  const [reviewAutostartEnabled, setReviewAutostartEnabled] = useState(true);
  const [selections, setSelections] = useState<Record<ModelPolicyRole, string>>({
    reviewer_standard: PLATFORM_DEFAULT,
    reviewer_deep: PLATFORM_DEFAULT,
    reviewer_critical: PLATFORM_DEFAULT,
    judge: PLATFORM_DEFAULT,
  });

  useEffect(() => {
    if (workspaceSettings.data) {
      setReviewAutostartEnabled(workspaceSettings.data.review_autostart_enabled);
    }
  }, [workspaceSettings.data]);

  useEffect(() => {
    if (!modelPolicy.data) return;
    setSelections({
      reviewer_standard: selectionValue(modelPolicy.data.overrides.reviewer_standard),
      reviewer_deep: selectionValue(modelPolicy.data.overrides.reviewer_deep),
      reviewer_critical: selectionValue(modelPolicy.data.overrides.reviewer_critical),
      judge: selectionValue(modelPolicy.data.overrides.judge),
    });
  }, [modelPolicy.data]);

  const catalogByRole = modelCatalog.data?.roles ?? {};

  async function handleAutostartToggle(enabled: boolean) {
    if (!workspaceId) return;
    const previous = reviewAutostartEnabled;
    setReviewAutostartEnabled(enabled);
    try {
      await patchWorkspace.mutateAsync({ review_autostart_enabled: enabled });
      notify.success(t('settings.review.autostartSaveSuccess'));
    } catch (error) {
      setReviewAutostartEnabled(previous);
      showDomainErrorToast(mapApiError(error));
    }
  }

  async function handleSaveModels() {
    if (!workspaceId || !modelPolicy.data) return;
    const payload: Partial<Record<ModelPolicyRole, ModelPolicyEntry | null>> = {};
    for (const role of MODEL_ROLES) {
      const nextValue = selections[role];
      const currentValue = selectionValue(modelPolicy.data.overrides[role]);
      if (nextValue === currentValue) continue;
      payload[role] = entryFromKey(nextValue);
    }
    if (Object.keys(payload).length === 0) {
      return;
    }
    try {
      await patchModelPolicy.mutateAsync(payload);
      notify.success(t('settings.review.modelsSaveSuccess'));
    } catch (error) {
      showDomainErrorToast(mapApiError(error));
    }
  }

  function renderOptions(items: ModelCatalogItem[] | undefined) {
    return (
      <>
        <QuietSelectItem value={PLATFORM_DEFAULT}>
          {t('settings.review.platformDefault')}
        </QuietSelectItem>
        {(items ?? []).map((item) => (
          <QuietSelectItem key={modelKey(item)} value={modelKey(item)}>
            {item.display_name}
          </QuietSelectItem>
        ))}
      </>
    );
  }

  if (!user?.workspace_id) {
    return null;
  }

  return (
    <div className="space-y-8">
      <h1 className="text-xl font-semibold text-[color:var(--app-text-strong)]">
        {t('settings.nav.review')}
      </h1>

      <section className="max-w-lg space-y-2">
        <h2 className="text-base font-medium text-[color:var(--app-text-strong)]">
          {t('settings.review.automationTitle')}
        </h2>
        <p className="text-sm text-[color:var(--app-text-muted)]">
          {t('settings.review.automationBody')}
        </p>
        <label className="flex items-center gap-3">
          <input
            type="checkbox"
            checked={reviewAutostartEnabled}
            disabled={patchWorkspace.isPending || workspaceSettings.isLoading}
            onChange={(event) => void handleAutostartToggle(event.target.checked)}
            className="size-4 rounded border-[color:var(--app-border-strong)]"
          />
          <span className="text-sm text-[color:var(--app-text-strong)]">
            {t('settings.review.autostartLabel')}
          </span>
        </label>
      </section>

      <section className="max-w-lg space-y-4 border-t border-[color:var(--app-border-subtle)] pt-6">
        <div className="space-y-1">
          <h2 className="text-base font-medium text-[color:var(--app-text-strong)]">
            {t('settings.review.modelsTitle')}
          </h2>
          <p className="text-sm text-[color:var(--app-text-muted)]">
            {t('settings.review.modelsBody')}
          </p>
          <p className="text-xs text-[color:var(--app-text-muted)]">
            {t('settings.review.modelsProRequired')}
          </p>
        </div>

        {MODEL_ROLES.map((role) => (
          <label key={role} className="block space-y-1">
            <span className="text-sm text-[color:var(--app-text-muted)]">
              {t(`settings.review.roles.${role}`)}
            </span>
            <QuietSelect
              value={selections[role]}
              onValueChange={(value) =>
                setSelections((current) => ({ ...current, [role]: value }))
              }
              disabled
            >
              <QuietSelectTrigger fullWidth>
                <QuietSelectValue />
              </QuietSelectTrigger>
              <QuietSelectContent>{renderOptions(catalogByRole[role])}</QuietSelectContent>
            </QuietSelect>
          </label>
        ))}

        <button
          type="button"
          disabled
          onClick={() => void handleSaveModels()}
          className="min-h-11 rounded-lg bg-[color:var(--app-cta-bg)] px-4 text-sm font-medium text-[color:var(--app-cta-fg)] focus-visible:ring-2 ring-[color:var(--app-ring-strong)] disabled:opacity-50"
        >
          {t('common.save')}
        </button>
      </section>
    </div>
  );
}
