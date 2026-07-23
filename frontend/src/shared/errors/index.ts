// frontend/src/shared/errors/index.ts
export * from './types';
export { mapApiError } from './errorMapper';
export { notify, showDomainErrorToast } from './toasts';
export { handleError, configureErrorHandling } from './handlers';
export { handleFormError } from './formErrors';
