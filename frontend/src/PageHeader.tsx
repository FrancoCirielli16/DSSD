import { Link } from "react-router-dom";
import type { ReactNode } from "react";

type Props = {
  to: string;
  label?: string;
  kicker?: string;
  title: string;
  lede?: string;
  action?: ReactNode;
};

export function PageHeader({ to, label = "Volver", kicker, title, lede, action }: Props) {
  return (
    <div className="page-header">
      <Link className="back-link" to={to}>
        <span aria-hidden>←</span> {label}
      </Link>
      <div className="page-head">
        <div>
          {kicker && <p className="kicker">{kicker}</p>}
          <h1 className="title page-title">{title}</h1>
          {lede && <p className="lede">{lede}</p>}
        </div>
        {action}
      </div>
    </div>
  );
}
