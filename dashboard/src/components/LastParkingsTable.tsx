import React, { useState } from 'react';
import { Table, Pagination, PaginationItem, PaginationLink } from 'reactstrap';

interface Column {
    text: string;
    dataField: string;
    formatter?: (value: any) => string;
    headerStyle?: React.CSSProperties;
    attrs?: Record<string, string>;
}

interface LastParkingsTableProps {
    data: any[];
    columns: Column[];
    keyField: string;
}

const LastParkingsTable: React.FC<LastParkingsTableProps> = ({ data, columns, keyField }) => {
    const [currentPage, setCurrentPage] = useState(1);
    const itemsPerPage = 17;

    // Calculate pagination
    const totalPages = Math.ceil(data.length / itemsPerPage);
    const startIndex = (currentPage - 1) * itemsPerPage;
    const endIndex = startIndex + itemsPerPage;
    const currentData = data.slice(startIndex, endIndex);

    // Handle page change
    const handlePageChange = (page: number) => {
        if (page >= 1 && page <= totalPages) {
            setCurrentPage(page);
        }
    };

    // Generate page numbers to display
    const getPageNumbers = () => {
        const pages: (number | string)[] = [];
        const maxPagesToShow = 5;
        
        if (totalPages <= maxPagesToShow) {
            for (let i = 1; i <= totalPages; i++) {
                pages.push(i);
            }
        } else {
            if (currentPage <= 3) {
                for (let i = 1; i <= 4; i++) {
                    pages.push(i);
                }
                pages.push('...');
                pages.push(totalPages);
            } else if (currentPage >= totalPages - 2) {
                pages.push(1);
                pages.push('...');
                for (let i = totalPages - 3; i <= totalPages; i++) {
                    pages.push(i);
                }
            } else {
                pages.push(1);
                pages.push('...');
                pages.push(currentPage - 1);
                pages.push(currentPage);
                pages.push(currentPage + 1);
                pages.push('...');
                pages.push(totalPages);
            }
        }
        
        return pages;
    };

    return (
        <div>
            <Table>
                <thead>
                    <tr>
                        {columns.map((column, index) => (
                            <th key={index} style={column.headerStyle} {...column.attrs}>
                                {column.text}
                            </th>
                        ))}
                    </tr>
                </thead>
                <tbody>
                    {currentData.map((row) => (
                        <tr key={row[keyField]}>
                            {columns.map((column, index) => {
                                const value = row[column.dataField];
                                const displayValue = column.formatter 
                                    ? column.formatter(value) 
                                    : value;
                                return (
                                    <td key={index} {...column.attrs}>
                                        {displayValue}
                                    </td>
                                );
                            })}
                        </tr>
                    ))}
                </tbody>
            </Table>
            

                <div className="d-flex justify-content-between align-items-center">
                    <div>
                        Showing {startIndex + 1} to {Math.min(endIndex, data.length)} of {data.length} entries
                    </div>
                    <Pagination>
                        <PaginationItem disabled={currentPage === 1}>
                            <PaginationLink previous onClick={() => handlePageChange(currentPage - 1)} />
                        </PaginationItem>
                        
                        {getPageNumbers().map((page, index) => (
                            typeof page === 'number' ? (
                                <PaginationItem key={index} active={page === currentPage}>
                                    <PaginationLink onClick={() => handlePageChange(page)}>
                                        {page}
                                    </PaginationLink>
                                </PaginationItem>
                            ) : (
                                <PaginationItem key={index} disabled>
                                    <PaginationLink>...</PaginationLink>
                                </PaginationItem>
                            )
                        ))}
                        
                        <PaginationItem disabled={currentPage === totalPages}>
                            <PaginationLink next onClick={() => handlePageChange(currentPage + 1)} />
                        </PaginationItem>
                    </Pagination>
                </div>

        </div>
    );
};

export default LastParkingsTable;

