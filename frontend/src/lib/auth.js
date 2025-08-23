export const ACCESS = "applymate_token";
export const REFRESH = "applymate_refresh";
export const setTokens = ({access, refresh}) => {
  if (access)  localStorage.setItem(ACCESS, access);
  if (refresh) localStorage.setItem(REFRESH, refresh);
};
export const getAccess  = () => localStorage.getItem(ACCESS)  || "";
export const getRefresh = () => localStorage.getItem(REFRESH) || "";
export const clearToken = () => { localStorage.removeItem(ACCESS); localStorage.removeItem(REFRESH); };
export const isAuthed = () => !!getAccess();
