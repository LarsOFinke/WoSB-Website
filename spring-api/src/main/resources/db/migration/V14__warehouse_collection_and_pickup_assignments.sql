alter table warehouse_entries
    add column collection_status varchar(32) not null default 'in_warehouse';

alter table warehouse_entries
    add constraint warehouse_entries_collection_status_check
        check (collection_status in ('up_for_collection', 'in_warehouse'));

create table fleet_warehouse_port_assignments (
    fleet_id bigint not null references fleets(id) on delete cascade,
    port_id bigint not null references warehouse_ports(id) on delete cascade,
    assignee_user_id bigint references users(id) on delete set null,
    updated_at timestamp not null,
    updated_by_id bigint references users(id) on delete set null,
    primary key (fleet_id, port_id)
);

create index fleet_warehouse_port_assignments_assignee_idx
    on fleet_warehouse_port_assignments (assignee_user_id);
