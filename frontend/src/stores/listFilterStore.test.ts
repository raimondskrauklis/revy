// frontend/src/stores/listFilterStore.test.ts
import { describe, expect, it } from 'vitest';
import {
  ITEM_FILTER_DEFAULTS,
  buildFilterUrlParams,
  filterStateToListParams,
  parseFilterUrlParams,
} from './listFilterStore';

describe('listFilterStore URL round-trip', () => {
  it('omits defaults from URL', () => {
    const params = buildFilterUrlParams({ ...ITEM_FILTER_DEFAULTS });
    expect(params.toString()).toBe('');
  });

  it('serializes active filters', () => {
    const params = buildFilterUrlParams({
      searchQuery: '  alpha  ',
      status: 'active',
      sort: 'name_asc',
    });
    expect(params.get('q')).toBe('alpha');
    expect(params.get('status')).toBe('active');
    expect(params.get('sort')).toBe('name_asc');
  });

  it('parses URL into partial state', () => {
    const parsed = parseFilterUrlParams(
      new URLSearchParams('q=beta&status=archived&sort=created_at_desc'),
    );
    expect(parsed).toEqual({
      searchQuery: 'beta',
      status: 'archived',
      sort: 'created_at_desc',
    });
  });

  it('maps to API params with min search length', () => {
    expect(filterStateToListParams({ ...ITEM_FILTER_DEFAULTS, searchQuery: 'a' })).toEqual({});
    expect(
      filterStateToListParams({
        searchQuery: 'ok',
        status: 'active',
        sort: ITEM_FILTER_DEFAULTS.sort,
      }),
    ).toEqual({ search: 'ok', status: 'active' });
  });
});
