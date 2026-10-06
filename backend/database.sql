-- Apexive Community database bootstrap
-- PostgreSQL 14+; run once against a newly created, empty database.
-- Generated from backend/app/models and aligned to the current Alembic head.
-- This creates the complete application schema; it does not create users or credentials.

BEGIN;


CREATE TABLE categories (
	id SERIAL NOT NULL, 
	name VARCHAR(120) NOT NULL, 
	slug VARCHAR(140) NOT NULL, 
	description TEXT NOT NULL, 
	parent_id INTEGER, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(parent_id) REFERENCES categories (id) ON DELETE CASCADE
)

;

CREATE UNIQUE INDEX ix_categories_slug ON categories (slug);

CREATE UNIQUE INDEX ix_categories_name ON categories (name);

CREATE INDEX ix_categories_parent_id ON categories (parent_id);


CREATE TABLE tenants (
	id SERIAL NOT NULL, 
	name VARCHAR(200) NOT NULL, 
	slug VARCHAR(240) NOT NULL, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (id)
)

;

CREATE UNIQUE INDEX ix_tenants_slug ON tenants (slug);


CREATE TABLE subscription_plans (
	id SERIAL NOT NULL, 
	product_key VARCHAR(100) NOT NULL, 
	name VARCHAR(200) NOT NULL, 
	description TEXT NOT NULL, 
	monthly_price NUMERIC(12, 2) NOT NULL, 
	currency VARCHAR(10) NOT NULL, 
	billing_cycle VARCHAR(30) NOT NULL, 
	is_active BOOLEAN NOT NULL, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (id)
)

;

CREATE UNIQUE INDEX ix_subscription_plans_product_key ON subscription_plans (product_key);


CREATE TABLE users (
	id SERIAL NOT NULL, 
	tenant_id INTEGER, 
	username VARCHAR(50) NOT NULL, 
	email VARCHAR(255) NOT NULL, 
	password_hash VARCHAR(255) NOT NULL, 
	display_name VARCHAR(100) NOT NULL, 
	bio VARCHAR(500) NOT NULL, 
	is_active BOOLEAN NOT NULL, 
	is_admin BOOLEAN NOT NULL, 
	email_verified_at TIMESTAMP WITHOUT TIME ZONE, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(tenant_id) REFERENCES tenants (id) ON DELETE SET NULL
)

;

CREATE UNIQUE INDEX ix_users_username ON users (username);

CREATE INDEX ix_users_tenant_id ON users (tenant_id);

CREATE UNIQUE INDEX ix_users_email ON users (email);


CREATE TABLE subscriptions (
	id SERIAL NOT NULL, 
	tenant_id INTEGER NOT NULL, 
	plan_id INTEGER NOT NULL, 
	status VARCHAR(30) NOT NULL, 
	price NUMERIC(12, 2) NOT NULL, 
	currency VARCHAR(10) NOT NULL, 
	billing_cycle VARCHAR(30) NOT NULL, 
	start_date TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	current_period_end TIMESTAMP WITHOUT TIME ZONE, 
	cancelled_at TIMESTAMP WITHOUT TIME ZONE, 
	external_subscription_id VARCHAR(255), 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(tenant_id) REFERENCES tenants (id) ON DELETE CASCADE, 
	FOREIGN KEY(plan_id) REFERENCES subscription_plans (id) ON DELETE RESTRICT
)

;

CREATE INDEX ix_subscriptions_plan_id ON subscriptions (plan_id);

CREATE INDEX ix_subscriptions_status ON subscriptions (status);

CREATE INDEX ix_subscriptions_external_subscription_id ON subscriptions (external_subscription_id);

CREATE INDEX ix_subscriptions_tenant_id ON subscriptions (tenant_id);


CREATE TABLE threads (
	id SERIAL NOT NULL, 
	title VARCHAR(300) NOT NULL, 
	slug VARCHAR(340) NOT NULL, 
	content TEXT NOT NULL, 
	problem TEXT, 
	network_environment TEXT, 
	symptoms TEXT, 
	logs_alarms TEXT, 
	what_i_tried TEXT, 
	category_id INTEGER NOT NULL, 
	author_id INTEGER NOT NULL, 
	views INTEGER NOT NULL, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(category_id) REFERENCES categories (id), 
	FOREIGN KEY(author_id) REFERENCES users (id)
)

;

CREATE UNIQUE INDEX ix_threads_slug ON threads (slug);

CREATE INDEX ix_threads_author_id ON threads (author_id);

CREATE INDEX ix_threads_title ON threads (title);

CREATE INDEX ix_threads_category_id ON threads (category_id);


CREATE TABLE email_verification_tokens (
	id SERIAL NOT NULL, 
	user_id INTEGER NOT NULL, 
	token_hash VARCHAR(255) NOT NULL, 
	expires_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	used_at TIMESTAMP WITHOUT TIME ZONE, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(user_id) REFERENCES users (id), 
	UNIQUE (token_hash)
)

;

CREATE INDEX ix_email_verification_tokens_user_id ON email_verification_tokens (user_id);


CREATE TABLE password_reset_tokens (
	id SERIAL NOT NULL, 
	user_id INTEGER NOT NULL, 
	token_hash VARCHAR(255) NOT NULL, 
	expires_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	used_at TIMESTAMP WITHOUT TIME ZONE, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(user_id) REFERENCES users (id) ON DELETE CASCADE
)

;

CREATE UNIQUE INDEX ix_password_reset_tokens_token_hash ON password_reset_tokens (token_hash);

CREATE INDEX ix_password_reset_tokens_user_id ON password_reset_tokens (user_id);


CREATE TABLE articles (
	id SERIAL NOT NULL, 
	title VARCHAR(300) NOT NULL, 
	slug VARCHAR(340) NOT NULL, 
	excerpt VARCHAR(600) NOT NULL, 
	content TEXT NOT NULL, 
	category VARCHAR(100) NOT NULL, 
	author_id INTEGER NOT NULL, 
	cover_image_url VARCHAR(1000), 
	read_time_minutes INTEGER NOT NULL, 
	views INTEGER NOT NULL, 
	is_published BOOLEAN NOT NULL, 
	is_featured BOOLEAN NOT NULL, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(author_id) REFERENCES users (id)
)

;

CREATE INDEX ix_articles_category ON articles (category);

CREATE INDEX ix_articles_title ON articles (title);

CREATE INDEX ix_articles_is_published ON articles (is_published);

CREATE UNIQUE INDEX ix_articles_slug ON articles (slug);

CREATE INDEX ix_articles_author_id ON articles (author_id);

CREATE INDEX ix_articles_is_featured ON articles (is_featured);


CREATE TABLE projects (
	id SERIAL NOT NULL, 
	name VARCHAR(200) NOT NULL, 
	slug VARCHAR(240) NOT NULL, 
	description VARCHAR(800) NOT NULL, 
	content TEXT NOT NULL, 
	category VARCHAR(100) NOT NULL, 
	creator_id INTEGER NOT NULL, 
	repository_url VARCHAR(1000), 
	website_url VARCHAR(1000), 
	logo_url VARCHAR(1000), 
	status VARCHAR(50) NOT NULL, 
	stars INTEGER NOT NULL, 
	views INTEGER NOT NULL, 
	is_featured BOOLEAN NOT NULL, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(creator_id) REFERENCES users (id)
)

;

CREATE INDEX ix_projects_creator_id ON projects (creator_id);

CREATE UNIQUE INDEX ix_projects_slug ON projects (slug);

CREATE INDEX ix_projects_status ON projects (status);

CREATE INDEX ix_projects_category ON projects (category);

CREATE INDEX ix_projects_is_featured ON projects (is_featured);

CREATE INDEX ix_projects_name ON projects (name);


CREATE TABLE resources (
	id SERIAL NOT NULL, 
	title VARCHAR(300) NOT NULL, 
	slug VARCHAR(340) NOT NULL, 
	description VARCHAR(800) NOT NULL, 
	content TEXT NOT NULL, 
	resource_type VARCHAR(50) NOT NULL, 
	category VARCHAR(100) NOT NULL, 
	author_id INTEGER NOT NULL, 
	file_url VARCHAR(1000), 
	file_size VARCHAR(50), 
	downloads INTEGER NOT NULL, 
	is_featured BOOLEAN NOT NULL, 
	is_published BOOLEAN NOT NULL, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(author_id) REFERENCES users (id)
)

;

CREATE INDEX ix_resources_title ON resources (title);

CREATE UNIQUE INDEX ix_resources_slug ON resources (slug);

CREATE INDEX ix_resources_is_featured ON resources (is_featured);

CREATE INDEX ix_resources_author_id ON resources (author_id);

CREATE INDEX ix_resources_is_published ON resources (is_published);

CREATE INDEX ix_resources_resource_type ON resources (resource_type);

CREATE INDEX ix_resources_category ON resources (category);


CREATE TABLE tenant_documents (
	id SERIAL NOT NULL, 
	tenant_id INTEGER NOT NULL, 
	owner_id INTEGER NOT NULL, 
	title VARCHAR(300) NOT NULL, 
	document_type VARCHAR(100) NOT NULL, 
	content TEXT NOT NULL, 
	status VARCHAR(50) NOT NULL, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(tenant_id) REFERENCES tenants (id) ON DELETE CASCADE, 
	FOREIGN KEY(owner_id) REFERENCES users (id)
)

;

CREATE INDEX ix_tenant_documents_owner_id ON tenant_documents (owner_id);

CREATE INDEX ix_tenant_documents_tenant_id ON tenant_documents (tenant_id);


CREATE TABLE tenant_workflows (
	id SERIAL NOT NULL, 
	tenant_id INTEGER NOT NULL, 
	created_by_id INTEGER NOT NULL, 
	name VARCHAR(200) NOT NULL, 
	workflow_type VARCHAR(100) NOT NULL, 
	status VARCHAR(50) NOT NULL, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(tenant_id) REFERENCES tenants (id) ON DELETE CASCADE, 
	FOREIGN KEY(created_by_id) REFERENCES users (id)
)

;

CREATE INDEX ix_tenant_workflows_tenant_id ON tenant_workflows (tenant_id);


CREATE TABLE tenant_audit_logs (
	id SERIAL NOT NULL, 
	tenant_id INTEGER NOT NULL, 
	actor_id INTEGER, 
	action VARCHAR(100) NOT NULL, 
	entity_type VARCHAR(100) NOT NULL, 
	entity_id VARCHAR(100), 
	details TEXT NOT NULL, 
	old_value TEXT, 
	new_value TEXT, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(tenant_id) REFERENCES tenants (id) ON DELETE CASCADE, 
	FOREIGN KEY(actor_id) REFERENCES users (id)
)

;

CREATE INDEX ix_tenant_audit_logs_tenant_id ON tenant_audit_logs (tenant_id);


CREATE TABLE notifications (
	id SERIAL NOT NULL, 
	recipient_id INTEGER NOT NULL, 
	actor_id INTEGER, 
	type VARCHAR(50) NOT NULL, 
	title VARCHAR(200) NOT NULL, 
	message TEXT NOT NULL, 
	link VARCHAR(500), 
	entity_type VARCHAR(50), 
	entity_id INTEGER, 
	is_read BOOLEAN NOT NULL, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(recipient_id) REFERENCES users (id), 
	FOREIGN KEY(actor_id) REFERENCES users (id)
)

;

CREATE INDEX ix_notifications_is_read ON notifications (is_read);

CREATE INDEX ix_notifications_recipient_id ON notifications (recipient_id);

CREATE INDEX ix_notifications_created_at ON notifications (created_at);

CREATE INDEX ix_notifications_type ON notifications (type);

CREATE INDEX ix_notifications_actor_id ON notifications (actor_id);


CREATE TABLE workflow_executions (
	id SERIAL NOT NULL, 
	tenant_id INTEGER NOT NULL, 
	requested_by_id INTEGER NOT NULL, 
	workflow_name VARCHAR(200) NOT NULL, 
	status VARCHAR(50) NOT NULL, 
	current_step VARCHAR(100) NOT NULL, 
	input_payload TEXT NOT NULL, 
	result_payload TEXT NOT NULL, 
	checkpoint TEXT, 
	version INTEGER NOT NULL, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(tenant_id) REFERENCES tenants (id) ON DELETE CASCADE, 
	FOREIGN KEY(requested_by_id) REFERENCES users (id)
)

;

CREATE INDEX ix_workflow_executions_status ON workflow_executions (status);

CREATE INDEX ix_workflow_executions_tenant_id ON workflow_executions (tenant_id);


CREATE TABLE billing_events (
	id SERIAL NOT NULL, 
	tenant_id INTEGER NOT NULL, 
	subscription_id INTEGER, 
	event_type VARCHAR(100) NOT NULL, 
	status VARCHAR(50) NOT NULL, 
	external_event_id VARCHAR(255), 
	amount NUMERIC(12, 2), 
	currency VARCHAR(10) NOT NULL, 
	details TEXT NOT NULL, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(tenant_id) REFERENCES tenants (id) ON DELETE CASCADE, 
	FOREIGN KEY(subscription_id) REFERENCES subscriptions (id) ON DELETE SET NULL
)

;

CREATE INDEX ix_billing_events_subscription_id ON billing_events (subscription_id);

CREATE INDEX ix_billing_events_tenant_id ON billing_events (tenant_id);

CREATE UNIQUE INDEX ix_billing_events_external_event_id ON billing_events (external_event_id);

CREATE INDEX ix_billing_events_event_type ON billing_events (event_type);


CREATE TABLE payments (
	id SERIAL NOT NULL, 
	tenant_id INTEGER NOT NULL, 
	plan_id INTEGER NOT NULL, 
	subscription_id INTEGER, 
	provider VARCHAR(50) NOT NULL, 
	payment_method VARCHAR(50) NOT NULL, 
	status VARCHAR(30) NOT NULL, 
	amount NUMERIC(12, 2) NOT NULL, 
	currency VARCHAR(10) NOT NULL, 
	checkout_reference VARCHAR(255), 
	external_payment_id VARCHAR(255), 
	failure_reason TEXT, 
	paid_at TIMESTAMP WITHOUT TIME ZONE, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(tenant_id) REFERENCES tenants (id) ON DELETE CASCADE, 
	FOREIGN KEY(plan_id) REFERENCES subscription_plans (id) ON DELETE RESTRICT, 
	FOREIGN KEY(subscription_id) REFERENCES subscriptions (id) ON DELETE SET NULL
)

;

CREATE INDEX ix_payments_tenant_id ON payments (tenant_id);

CREATE INDEX ix_payments_plan_id ON payments (plan_id);

CREATE UNIQUE INDEX ix_payments_external_payment_id ON payments (external_payment_id);

CREATE INDEX ix_payments_payment_method ON payments (payment_method);

CREATE INDEX ix_payments_status ON payments (status);

CREATE UNIQUE INDEX ix_payments_checkout_reference ON payments (checkout_reference);

CREATE INDEX ix_payments_subscription_id ON payments (subscription_id);

CREATE INDEX ix_payments_provider ON payments (provider);


CREATE TABLE replies (
	id SERIAL NOT NULL, 
	content TEXT NOT NULL, 
	thread_id INTEGER NOT NULL, 
	author_id INTEGER NOT NULL, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(thread_id) REFERENCES threads (id), 
	FOREIGN KEY(author_id) REFERENCES users (id)
)

;

CREATE INDEX ix_replies_author_id ON replies (author_id);

CREATE INDEX ix_replies_thread_id ON replies (thread_id);


CREATE TABLE tenant_permissions (
	id SERIAL NOT NULL, 
	tenant_id INTEGER NOT NULL, 
	user_id INTEGER NOT NULL, 
	document_id INTEGER, 
	permission VARCHAR(50) NOT NULL, 
	granted BOOLEAN NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(tenant_id) REFERENCES tenants (id) ON DELETE CASCADE, 
	FOREIGN KEY(user_id) REFERENCES users (id) ON DELETE CASCADE, 
	FOREIGN KEY(document_id) REFERENCES tenant_documents (id) ON DELETE CASCADE
)

;

CREATE INDEX ix_tenant_permissions_user_id ON tenant_permissions (user_id);

CREATE INDEX ix_tenant_permissions_tenant_id ON tenant_permissions (tenant_id);

CREATE INDEX ix_tenant_permissions_document_id ON tenant_permissions (document_id);


CREATE TABLE project_technologies (
	id SERIAL NOT NULL, 
	project_id INTEGER NOT NULL, 
	name VARCHAR(100) NOT NULL, 
	PRIMARY KEY (id), 
	CONSTRAINT uq_project_technology UNIQUE (project_id, name), 
	FOREIGN KEY(project_id) REFERENCES projects (id) ON DELETE CASCADE
)

;

CREATE INDEX ix_project_technologies_project_id ON project_technologies (project_id);


CREATE TABLE project_likes (
	id SERIAL NOT NULL, 
	project_id INTEGER NOT NULL, 
	user_id INTEGER NOT NULL, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	CONSTRAINT uq_project_like UNIQUE (project_id, user_id), 
	FOREIGN KEY(project_id) REFERENCES projects (id) ON DELETE CASCADE, 
	FOREIGN KEY(user_id) REFERENCES users (id) ON DELETE CASCADE
)

;

CREATE INDEX ix_project_likes_user_id ON project_likes (user_id);

CREATE INDEX ix_project_likes_project_id ON project_likes (project_id);


CREATE TABLE project_bookmarks (
	id SERIAL NOT NULL, 
	project_id INTEGER NOT NULL, 
	user_id INTEGER NOT NULL, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	CONSTRAINT uq_project_bookmark UNIQUE (project_id, user_id), 
	FOREIGN KEY(project_id) REFERENCES projects (id) ON DELETE CASCADE, 
	FOREIGN KEY(user_id) REFERENCES users (id) ON DELETE CASCADE
)

;

CREATE INDEX ix_project_bookmarks_user_id ON project_bookmarks (user_id);

CREATE INDEX ix_project_bookmarks_project_id ON project_bookmarks (project_id);


CREATE TABLE project_follows (
	id SERIAL NOT NULL, 
	project_id INTEGER NOT NULL, 
	user_id INTEGER NOT NULL, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	CONSTRAINT uq_project_follow UNIQUE (project_id, user_id), 
	FOREIGN KEY(project_id) REFERENCES projects (id) ON DELETE CASCADE, 
	FOREIGN KEY(user_id) REFERENCES users (id) ON DELETE CASCADE
)

;

CREATE INDEX ix_project_follows_user_id ON project_follows (user_id);

CREATE INDEX ix_project_follows_project_id ON project_follows (project_id);


CREATE TABLE project_embeddings (
	id SERIAL NOT NULL, 
	project_id INTEGER NOT NULL, 
	model VARCHAR(100) NOT NULL, 
	vector TEXT NOT NULL, 
	dimensions INTEGER NOT NULL, 
	updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	UNIQUE (project_id), 
	FOREIGN KEY(project_id) REFERENCES projects (id) ON DELETE CASCADE
)

;


CREATE TABLE reputation_events (
	id SERIAL NOT NULL, 
	user_id INTEGER NOT NULL, 
	project_id INTEGER, 
	event_type VARCHAR(100) NOT NULL, 
	points INTEGER NOT NULL, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(user_id) REFERENCES users (id) ON DELETE CASCADE, 
	FOREIGN KEY(project_id) REFERENCES projects (id) ON DELETE CASCADE
)

;

CREATE INDEX ix_reputation_events_user_id ON reputation_events (user_id);

CREATE INDEX ix_reputation_events_event_type ON reputation_events (event_type);

CREATE INDEX ix_reputation_events_project_id ON reputation_events (project_id);


CREATE TABLE workflow_execution_events (
	id SERIAL NOT NULL, 
	execution_id INTEGER NOT NULL, 
	tenant_id INTEGER NOT NULL, 
	actor_id INTEGER, 
	event_type VARCHAR(100) NOT NULL, 
	status VARCHAR(50) NOT NULL, 
	details TEXT NOT NULL, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(execution_id) REFERENCES workflow_executions (id) ON DELETE CASCADE, 
	FOREIGN KEY(tenant_id) REFERENCES tenants (id) ON DELETE CASCADE, 
	FOREIGN KEY(actor_id) REFERENCES users (id)
)

;

CREATE INDEX ix_workflow_execution_events_tenant_id ON workflow_execution_events (tenant_id);

CREATE INDEX ix_workflow_execution_events_execution_id ON workflow_execution_events (execution_id);

-- Seed the forum taxonomy without creating a default administrator account.
INSERT INTO categories (name, slug, description, created_at)
VALUES
    ('Artificial Intelligence', 'artificial-intelligence', 'AI agents, LLMs, machine learning and automation.', CURRENT_TIMESTAMP),
    ('Development', 'development', 'Web, mobile, backend and software engineering.', CURRENT_TIMESTAMP),
    ('Data & Cloud', 'data-cloud', 'Databases, cloud infrastructure and distributed systems.', CURRENT_TIMESTAMP),
    ('Security', 'security', 'Cybersecurity, application security and privacy.', CURRENT_TIMESTAMP),
    ('Telecom & Networking', 'telecom-networking', 'Core networks, radio access, IP transport, operations, security, and telecom power.', CURRENT_TIMESTAMP)
ON CONFLICT (slug) DO NOTHING;

INSERT INTO categories (name, slug, description, parent_id, created_at)
SELECT sections.name, sections.slug, sections.description, parent.id, CURRENT_TIMESTAMP
FROM (VALUES
    ('Core Network', 'core-network', 'Core Network topics in Telecom & Networking.'),
    ('Radio Access Network', 'radio-access-network', 'Radio Access Network topics in Telecom & Networking.'),
    ('IP & Transport', 'ip-transport', 'IP & Transport topics in Telecom & Networking.'),
    ('Network Operations', 'network-operations', 'Network Operations topics in Telecom & Networking.'),
    ('Telecom Security', 'telecom-security', 'Telecom Security topics in Telecom & Networking.'),
    ('Telecom Power', 'telecom-power', 'Telecom Power topics in Telecom & Networking.')
) AS sections(name, slug, description)
JOIN categories AS parent ON parent.slug = 'telecom-networking'
ON CONFLICT (slug) DO NOTHING;

INSERT INTO categories (name, slug, description, parent_id, created_at)
SELECT children.name, children.slug, children.description, parent.id, CURRENT_TIMESTAMP
FROM (VALUES
    ('EPC / 4G Core', 'epc-4g-core', 'EPC / 4G Core discussions in Core Network.'),
    ('5G Core', '5g-core', '5G Core discussions in Core Network.'),
    ('IMS', 'ims', 'IMS discussions in Core Network.'),
    ('Signaling', 'signaling', 'Signaling discussions in Core Network.')
) AS children(name, slug, description)
JOIN categories AS parent ON parent.slug = 'core-network'
ON CONFLICT (slug) DO NOTHING;

INSERT INTO categories (name, slug, description, parent_id, created_at)
SELECT children.name, children.slug, children.description, parent.id, CURRENT_TIMESTAMP
FROM (VALUES
    ('2G / GSM', '2g-gsm', '2G / GSM discussions in Radio Access Network.'),
    ('3G / UMTS', '3g-umts', '3G / UMTS discussions in Radio Access Network.'),
    ('4G / LTE', '4g-lte', '4G / LTE discussions in Radio Access Network.'),
    ('5G / NR', '5g-nr', '5G / NR discussions in Radio Access Network.')
) AS children(name, slug, description)
JOIN categories AS parent ON parent.slug = 'radio-access-network'
ON CONFLICT (slug) DO NOTHING;

INSERT INTO categories (name, slug, description, parent_id, created_at)
SELECT children.name, children.slug, children.description, parent.id, CURRENT_TIMESTAMP
FROM (VALUES
    ('IP Networking', 'ip-networking', 'IP Networking discussions in IP & Transport.'),
    ('MPLS', 'mpls', 'MPLS discussions in IP & Transport.'),
    ('Microwave', 'microwave', 'Microwave discussions in IP & Transport.'),
    ('Fiber', 'fiber', 'Fiber discussions in IP & Transport.'),
    ('SDN / SD-WAN', 'sdn-sd-wan', 'SDN / SD-WAN discussions in IP & Transport.')
) AS children(name, slug, description)
JOIN categories AS parent ON parent.slug = 'ip-transport'
ON CONFLICT (slug) DO NOTHING;

INSERT INTO categories (name, slug, description, parent_id, created_at)
SELECT children.name, children.slug, children.description, parent.id, CURRENT_TIMESTAMP
FROM (VALUES
    ('NOC', 'noc', 'NOC discussions in Network Operations.'),
    ('Monitoring', 'monitoring', 'Monitoring discussions in Network Operations.'),
    ('Troubleshooting', 'troubleshooting', 'Troubleshooting discussions in Network Operations.'),
    ('Performance', 'performance', 'Performance discussions in Network Operations.'),
    ('Network Automation', 'network-automation', 'Network Automation discussions in Network Operations.')
) AS children(name, slug, description)
JOIN categories AS parent ON parent.slug = 'network-operations'
ON CONFLICT (slug) DO NOTHING;

INSERT INTO categories (name, slug, description, parent_id, created_at)
SELECT children.name, children.slug, children.description, parent.id, CURRENT_TIMESTAMP
FROM (VALUES
    ('Network Security', 'network-security', 'Network Security discussions in Telecom Security.'),
    ('Signaling Security', 'signaling-security', 'Signaling Security discussions in Telecom Security.'),
    ('4G / 5G Security', '4g-5g-security', '4G / 5G Security discussions in Telecom Security.'),
    ('Fraud & Abuse', 'fraud-abuse', 'Fraud & Abuse discussions in Telecom Security.')
) AS children(name, slug, description)
JOIN categories AS parent ON parent.slug = 'telecom-security'
ON CONFLICT (slug) DO NOTHING;

INSERT INTO categories (name, slug, description, parent_id, created_at)
SELECT children.name, children.slug, children.description, parent.id, CURRENT_TIMESTAMP
FROM (VALUES
    ('Rectifier', 'rectifier', 'Rectifier discussions in Telecom Power.'),
    ('Battery', 'battery', 'Battery discussions in Telecom Power.'),
    ('Generator', 'generator', 'Generator discussions in Telecom Power.'),
    ('Solar', 'solar', 'Solar discussions in Telecom Power.'),
    ('Site Power', 'site-power', 'Site Power discussions in Telecom Power.')
) AS children(name, slug, description)
JOIN categories AS parent ON parent.slug = 'telecom-power'
ON CONFLICT (slug) DO NOTHING;

-- Seed only plans with confirmed prices; do not create unpriced products.
INSERT INTO subscription_plans (
    product_key, name, description, monthly_price, currency,
    billing_cycle, is_active, created_at
)
VALUES
    ('trademark', 'Trademark Conflict', 'AI-powered trademark conflict detection and analysis.', 249.00, 'USD', 'monthly', TRUE, CURRENT_TIMESTAMP),
    ('workforce', 'Autonomous Workforce', 'Governed autonomous enterprise AI workforce and workflow execution.', 299.00, 'USD', 'monthly', TRUE, CURRENT_TIMESTAMP)
ON CONFLICT (product_key) DO UPDATE
SET name = EXCLUDED.name,
    description = EXCLUDED.description,
    monthly_price = EXCLUDED.monthly_price,
    currency = EXCLUDED.currency,
    billing_cycle = EXCLUDED.billing_cycle,
    is_active = EXCLUDED.is_active;

CREATE TABLE alembic_version (
    version_num VARCHAR(32) NOT NULL,
    CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num)
);

INSERT INTO alembic_version (version_num) VALUES ('a1b2c3d4e5f6');

COMMIT;
