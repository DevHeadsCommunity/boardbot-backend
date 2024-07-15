import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Check, Minus } from "lucide-react";
import React from "react";

interface SortableTableProps {
  columns: TableColumn[];
  data: any[];
  onRowClick?: (rowData: any) => void;
}
export interface TableColumn {
  header: string;
  accessor: string;
  render?: (data: any) => React.ReactNode;
}
const SortableTable: React.FC<SortableTableProps> = ({
  columns,
  data,
  onRowClick,
}) => {
  const displayItem = (item: any) => {
    if (item === true) {
      return <Check size={18} strokeWidth={3} />;
    } else if (item === false) {
      return <Minus size={14} strokeWidth={2} />;
    } else {
      return item;
    }
  };

  return (
    <Table className="w-full">
      <TableHeader>
        <TableRow>
          {columns.map((column) => (
            <TableHead
              key={column.accessor}
              className=" align-middle duration-300 text-[16px] font-normal capitalize"
            >
              {column.header}
            </TableHead>
          ))}
        </TableRow>
      </TableHeader>
      <TableBody>
        {data.map((item, index) => (
          <TableRow className="" key={index} onClick={() => onRowClick?.(item)}>
            {columns.map((column) => (
              <TableCell
                key={column.accessor}
                className={`text-[14px] font-normal `}
              >
                {displayItem(item[column.accessor])}
              </TableCell>
            ))}
          </TableRow>
        ))}
      </TableBody>
    </Table>
  );
};

export default SortableTable;
