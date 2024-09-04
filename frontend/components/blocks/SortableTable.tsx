import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Check, ChevronDown, ChevronUp, Minus } from "lucide-react";
import React, { useMemo, useState } from "react";

export interface TableColumn {
  header: string;
  accessor: string;
  cell?: (value: any) => React.ReactNode;
  sortable?: boolean;
}

interface SortableTableProps {
  columns: TableColumn[];
  data: any[];
  onRowClick?: (rowData: any) => void;
}

const SortableTable: React.FC<SortableTableProps> = ({ columns, data, onRowClick }) => {
  const [sortConfig, setSortConfig] = useState<{ key: string; direction: "asc" | "desc" } | null>(null);

  const sortedData = useMemo(() => {
    let sortableItems = [...data];
    if (sortConfig !== null) {
      sortableItems.sort((a, b) => {
        if (a[sortConfig.key] < b[sortConfig.key]) {
          return sortConfig.direction === "asc" ? -1 : 1;
        }
        if (a[sortConfig.key] > b[sortConfig.key]) {
          return sortConfig.direction === "asc" ? 1 : -1;
        }
        return 0;
      });
    }
    return sortableItems;
  }, [data, sortConfig]);

  const requestSort = (key: string) => {
    let direction: "asc" | "desc" = "asc";
    if (sortConfig && sortConfig.key === key && sortConfig.direction === "asc") {
      direction = "desc";
    }
    setSortConfig({ key, direction });
  };

  const displayItem = (item: any, column: TableColumn) => {
    if (column.cell) {
      return column.cell(item);
    }

    if (item === true) {
      return <Check size={18} strokeWidth={3} className="text-green-500" />;
    } else if (item === false) {
      return <Minus size={14} strokeWidth={2} className="text-red-500" />;
    } else if (item instanceof Date) {
      return item.toLocaleString();
    } else if (typeof item === "object") {
      return JSON.stringify(item);
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
              className="align-middle text-[16px] font-semibold capitalize text-gray-700 duration-300"
              onClick={() => column.sortable && requestSort(column.accessor)}
              style={{ cursor: column.sortable ? "pointer" : "default" }}
            >
              <div className="flex items-center">
                {column.header}
                {column.sortable && sortConfig?.key === column.accessor && (sortConfig.direction === "asc" ? <ChevronUp size={14} /> : <ChevronDown size={14} />)}
              </div>
            </TableHead>
          ))}
        </TableRow>
      </TableHeader>
      <TableBody>
        {sortedData.map((item, index) => (
          <TableRow key={index} onClick={() => onRowClick?.(item)} className="cursor-pointer transition-colors duration-150 hover:bg-gray-50">
            {columns.map((column) => (
              <TableCell key={column.accessor} className="text-[14px] font-normal">
                {displayItem(item[column.accessor], column)}
              </TableCell>
            ))}
          </TableRow>
        ))}
      </TableBody>
    </Table>
  );
};

export default SortableTable;
