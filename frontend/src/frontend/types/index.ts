export type NavigationPage = 
  | 'crm' 
  | 'att' 
  | 'agenda' 
  | 'base' 
  | 'auto' 
  | 'canal' 
  | 'reports';

export type LeadStatus = 
  | 'novo' 
  | 'qualificando' 
  | 'orcamento' 
  | 'follow_up' 
  | 'negociando' 
  | 'agendado' 
  | 'ganho';

export interface Lead {
  id: string;
  n: string; // name
  t: string; // telephone
  st: LeadStatus;
  ev: string; // event date & type
  pc: string; // piece of interest
  or: string; // origin/channel
  v: number;  // estimated value
  h: string;  // time elapsed
  hot?: boolean;
  cold?: boolean;
  fu?: number; // follow-up count
  ag?: string; // scheduled date
}

export interface KanbanColumn {
  k: LeadStatus;
  n: string;
  c: string; // hex/var color
}

export interface FollowUpTemplate {
  n: string;
  c: string;
}

export interface ProductItem {
  n: string;
  d: string;
  p: string;
  g: [string, string]; // gradient colors
  k: 'd' | 's'; // dress or suit
}

export interface ChatStep {
  k: 'in' | 'ia' | 'ag' | 'api' | 'ctx' | 'sys' | 'ho';
  t?: string;
  key?: string;
  v?: string;
  h?: number;
  m?: string; // HTTP method
  p?: string; // path
  r?: string; // response
  w?: number; // warning / write flag
  warn?: boolean;
  prods?: ProductItem[];
}

export interface Scenario {
  id: string;
  t: string; // title
  h: string; // header subtitle
  c: { n: string; i: string; p: string };
  pv: string; // preview text
  ctx: [string, string, string?][];
  steps: ChatStep[];
  after?: ChatStep[];
}

export interface DayScheduleItem {
  t: string; // time
  w: string; // person name
  x: string; // service details
  b?: number; // automation flag (1 for automation, 0/undefined for store)
  k?: string; // 'at' for atendimento
}

export interface DaySchedule {
  d: string; // day label
  n: number; // day number
  i: DayScheduleItem[];
}

export interface ContactRecord {
  name: string;
  event: string;
  month: string;
  interest: string;
  status: 'Descartado' | 'Ganho' | 'Ativo';
  lastContact: string;
}

export interface AutomationRoutine {
  n: string; // name
  g: string; // trigger rule
  on: boolean;
  d: string; // description
  m: [string, string][]; // metrics
  ic: string; // icon type
}

export interface ProviderCapability {
  k: string; // key
  n: string; // name
  s: string; // subtitle
  ic: string; // color
  phone: string;
  caps: [string, string, 'y' | 'n' | 'r'][];
}

export interface ToastMessage {
  id: string;
  title: string;
  subtitle?: string;
}
