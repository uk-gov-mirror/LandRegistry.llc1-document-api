-- Create llc_document_db
CREATE DATABASE llc_document_db;

--Create user for llc_document DB
CREATE ROLE llc_document_user with LOGIN password 'llc_document_password';

\c llc_document_db;
CREATE EXTENSION postgis;