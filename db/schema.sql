\restrict dbmate

-- Dumped from database version 18.6
-- Dumped by pg_dump version 18.6

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET transaction_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: logins; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.logins (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    password_id uuid,
    user_agent text,
    client_ip inet NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL
);


--
-- Name: passwords; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.passwords (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    password text NOT NULL,
    access_level smallint NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL
);


--
-- Name: schema_migrations; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.schema_migrations (
    version character varying NOT NULL
);


--
-- Name: sessions; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.sessions (
    token uuid DEFAULT gen_random_uuid() NOT NULL,
    access_level smallint NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL
);


--
-- Name: logins logins_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.logins
    ADD CONSTRAINT logins_pkey PRIMARY KEY (id);


--
-- Name: passwords passwords_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.passwords
    ADD CONSTRAINT passwords_pkey PRIMARY KEY (id);


--
-- Name: schema_migrations schema_migrations_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.schema_migrations
    ADD CONSTRAINT schema_migrations_pkey PRIMARY KEY (version);


--
-- Name: sessions sessions_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.sessions
    ADD CONSTRAINT sessions_pkey PRIMARY KEY (token);


--
-- Name: logins logins_password_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.logins
    ADD CONSTRAINT logins_password_id_fkey FOREIGN KEY (password_id) REFERENCES public.passwords(id) ON DELETE SET NULL;


--
-- PostgreSQL database dump complete
--

\unrestrict dbmate


--
-- Dbmate schema migrations
--

INSERT INTO public.schema_migrations (version) VALUES
    ('20260827163942');
