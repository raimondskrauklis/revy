// frontend/src/lib/timezones.ts
export interface TimezoneOption {
  value: string;
  labelKey: string;
}

export const COMMON_TIMEZONES: TimezoneOption[] = [
  { value: 'UTC', labelKey: 'timezones.utc' },
  { value: 'Europe/Riga', labelKey: 'timezones.europeRiga' },
  { value: 'Europe/London', labelKey: 'timezones.europeLondon' },
  { value: 'Europe/Berlin', labelKey: 'timezones.europeBerlin' },
  { value: 'Europe/Paris', labelKey: 'timezones.europeParis' },
  { value: 'Europe/Helsinki', labelKey: 'timezones.europeHelsinki' },
  { value: 'Europe/Warsaw', labelKey: 'timezones.europeWarsaw' },
  { value: 'Europe/Stockholm', labelKey: 'timezones.europeStockholm' },
  { value: 'America/New_York', labelKey: 'timezones.americaNewYork' },
  { value: 'America/Chicago', labelKey: 'timezones.americaChicago' },
  { value: 'America/Denver', labelKey: 'timezones.americaDenver' },
  { value: 'America/Los_Angeles', labelKey: 'timezones.americaLosAngeles' },
  { value: 'America/Toronto', labelKey: 'timezones.americaToronto' },
  { value: 'America/Sao_Paulo', labelKey: 'timezones.americaSaoPaulo' },
  { value: 'Asia/Dubai', labelKey: 'timezones.asiaDubai' },
  { value: 'Asia/Kolkata', labelKey: 'timezones.asiaKolkata' },
  { value: 'Asia/Singapore', labelKey: 'timezones.asiaSingapore' },
  { value: 'Asia/Tokyo', labelKey: 'timezones.asiaTokyo' },
  { value: 'Australia/Sydney', labelKey: 'timezones.australiaSydney' },
  { value: 'Pacific/Auckland', labelKey: 'timezones.pacificAuckland' },
];
