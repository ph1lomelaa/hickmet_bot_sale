--
-- PostgreSQL database dump
--

\restrict bbeF9GwQSHd7bPLFxnq13JufKnGHmzm9eOEKTjI9vV9H8DXz7aF1p4YfdIy389w

-- Dumped from database version 17.7 (bdc8956)
-- Dumped by pg_dump version 17.7 (Homebrew)

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
-- Name: admin_settings; Type: TABLE; Schema: public; Owner: koyeb-adm
--

CREATE TABLE public.admin_settings (
    admin_id bigint NOT NULL,
    notify_new integer DEFAULT 0,
    notify_cancel integer DEFAULT 0,
    notify_reschedule integer DEFAULT 0,
    created_at timestamp without time zone DEFAULT now()
);


ALTER TABLE public.admin_settings OWNER TO "koyeb-adm";

--
-- Name: approval_requests; Type: TABLE; Schema: public; Owner: koyeb-adm
--

CREATE TABLE public.approval_requests (
    id integer NOT NULL,
    booking_id integer,
    request_type character varying,
    initiator_id bigint,
    status character varying DEFAULT 'pending'::character varying,
    created_at timestamp without time zone DEFAULT now(),
    comment text
);


ALTER TABLE public.approval_requests OWNER TO "koyeb-adm";

--
-- Name: approval_requests_id_seq; Type: SEQUENCE; Schema: public; Owner: koyeb-adm
--

CREATE SEQUENCE public.approval_requests_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.approval_requests_id_seq OWNER TO "koyeb-adm";

--
-- Name: approval_requests_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: koyeb-adm
--

ALTER SEQUENCE public.approval_requests_id_seq OWNED BY public.approval_requests.id;


--
-- Name: bookings; Type: TABLE; Schema: public; Owner: koyeb-adm
--

CREATE TABLE public.bookings (
    id integer NOT NULL,
    manager_id bigint,
    table_id character varying,
    sheet_name character varying,
    sheet_row_number integer,
    package_name character varying,
    region character varying,
    departure_city character varying,
    source character varying,
    amount_paid character varying,
    exchange_rate character varying,
    discount character varying,
    avia_request character varying,
    visa_status character varying,
    avia character varying,
    room_type character varying,
    meal_type character varying,
    train character varying,
    guest_last_name character varying,
    guest_first_name character varying,
    gender character varying,
    date_of_birth character varying,
    passport_num character varying,
    passport_expiry character varying,
    guest_iin character varying,
    contract_number character varying,
    price character varying,
    comment text,
    client_phone character varying,
    manager_name_text character varying,
    placement_type character varying,
    passport_image_path character varying,
    status character varying DEFAULT 'new'::character varying,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    group_members jsonb
);


ALTER TABLE public.bookings OWNER TO "koyeb-adm";

--
-- Name: рр; Type: TABLE; Schema: public; Owner: koyeb-adm
--

CREATE TABLE public."рр" (
    id integer NOT NULL,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    status character varying(50),
    guest_first_name character varying(100),
    guest_last_name character varying(100),
    package_name character varying(200),
    price numeric(10,2)
);


ALTER TABLE public."рр" OWNER TO "koyeb-adm";

--
-- Name: bookings_id_seq; Type: SEQUENCE; Schema: public; Owner: koyeb-adm
--

CREATE SEQUENCE public.bookings_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.bookings_id_seq OWNER TO "koyeb-adm";

--
-- Name: bookings_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: koyeb-adm
--

ALTER SEQUENCE public.bookings_id_seq OWNED BY public."рр".id;


--
-- Name: bookings_id_seq1; Type: SEQUENCE; Schema: public; Owner: koyeb-adm
--

CREATE SEQUENCE public.bookings_id_seq1
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.bookings_id_seq1 OWNER TO "koyeb-adm";

--
-- Name: bookings_id_seq1; Type: SEQUENCE OWNED BY; Schema: public; Owner: koyeb-adm
--

ALTER SEQUENCE public.bookings_id_seq1 OWNED BY public.bookings.id;


--
-- Name: requests_4u; Type: TABLE; Schema: public; Owner: koyeb-adm
--

CREATE TABLE public.requests_4u (
    id integer NOT NULL,
    manager_id bigint,
    manager_name character varying,
    table_id character varying,
    dates character varying,
    pilgrim_count integer,
    room_type character varying,
    status character varying,
    created_at timestamp without time zone,
    created_sheet_name character varying
);


ALTER TABLE public.requests_4u OWNER TO "koyeb-adm";

--
-- Name: requests_4u_id_seq; Type: SEQUENCE; Schema: public; Owner: koyeb-adm
--

CREATE SEQUENCE public.requests_4u_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.requests_4u_id_seq OWNER TO "koyeb-adm";

--
-- Name: requests_4u_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: koyeb-adm
--

ALTER SEQUENCE public.requests_4u_id_seq OWNED BY public.requests_4u.id;


--
-- Name: users; Type: TABLE; Schema: public; Owner: koyeb-adm
--

CREATE TABLE public.users (
    telegram_id bigint NOT NULL,
    full_name character varying,
    username character varying,
    role character varying,
    created_at timestamp without time zone
);


ALTER TABLE public.users OWNER TO "koyeb-adm";

--
-- Name: users_telegram_id_seq; Type: SEQUENCE; Schema: public; Owner: koyeb-adm
--

CREATE SEQUENCE public.users_telegram_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.users_telegram_id_seq OWNER TO "koyeb-adm";

--
-- Name: users_telegram_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: koyeb-adm
--

ALTER SEQUENCE public.users_telegram_id_seq OWNED BY public.users.telegram_id;


--
-- Name: approval_requests id; Type: DEFAULT; Schema: public; Owner: koyeb-adm
--

ALTER TABLE ONLY public.approval_requests ALTER COLUMN id SET DEFAULT nextval('public.approval_requests_id_seq'::regclass);


--
-- Name: bookings id; Type: DEFAULT; Schema: public; Owner: koyeb-adm
--

ALTER TABLE ONLY public.bookings ALTER COLUMN id SET DEFAULT nextval('public.bookings_id_seq1'::regclass);


--
-- Name: requests_4u id; Type: DEFAULT; Schema: public; Owner: koyeb-adm
--

ALTER TABLE ONLY public.requests_4u ALTER COLUMN id SET DEFAULT nextval('public.requests_4u_id_seq'::regclass);


--
-- Name: users telegram_id; Type: DEFAULT; Schema: public; Owner: koyeb-adm
--

ALTER TABLE ONLY public.users ALTER COLUMN telegram_id SET DEFAULT nextval('public.users_telegram_id_seq'::regclass);


--
-- Name: рр id; Type: DEFAULT; Schema: public; Owner: koyeb-adm
--

ALTER TABLE ONLY public."рр" ALTER COLUMN id SET DEFAULT nextval('public.bookings_id_seq'::regclass);


--
-- Data for Name: admin_settings; Type: TABLE DATA; Schema: public; Owner: koyeb-adm
--

COPY public.admin_settings (admin_id, notify_new, notify_cancel, notify_reschedule, created_at) FROM stdin;
8413412150	1	1	1	2025-12-29 23:51:12.330643
489877724	1	1	1	2025-12-30 07:01:34.161364
\.


--
-- Data for Name: approval_requests; Type: TABLE DATA; Schema: public; Owner: koyeb-adm
--

COPY public.approval_requests (id, booking_id, request_type, initiator_id, status, created_at, comment) FROM stdin;
\.


--
-- Data for Name: bookings; Type: TABLE DATA; Schema: public; Owner: koyeb-adm
--

COPY public.bookings (id, manager_id, table_id, sheet_name, sheet_row_number, package_name, region, departure_city, source, amount_paid, exchange_rate, discount, avia_request, visa_status, avia, room_type, meal_type, train, guest_last_name, guest_first_name, gender, date_of_birth, passport_num, passport_expiry, guest_iin, contract_number, price, comment, client_phone, manager_name_text, placement_type, passport_image_path, status, created_at, group_members) FROM stdin;
284	6253997402	15iaUA4J5rgfAz6isS6BA07idUA9dXl-BW15FMw--7Vg	25.01-01.02 NQZ-MED/7days	57	25.01-01.02  IZI/7 days	-	Astana	-	350	495	-	-	-	-	Triple	HB	-	SABIT	RAMAZAN	M	11.01.1999	N17173759	03.09.2024	990111350212	-	2250	-	-	AKZHOL	separate	/app/bull_project/bull_bot/tmp/uploads/bot_upload_1767166018905.png	new	2025-12-31 07:46:13.851786	["SABIT RAMAZAN"]
4	8348971315	15iaUA4J5rgfAz6isS6BA07idUA9dXl-BW15FMw--7Vg	07.01-14.01 Ala-Jed/AA/7days	5	07.01-14.01 NIYET econom/7 days	-	Almaty	-	980	495	-	-	-	-	Double	HB	-	YESMURZAYEV	BAURZHAN	M	23.07.1987	11598952	08.02.2028	870723302106	-	1080	5000kazhy \n	-	Nazerke	family	/app/bull_project/bull_bot/tmp/uploads/bot_upload_1766733648850.png	new	2025-12-26 07:22:28.640759	\N
138	6253997402	1r83RRUKrTQT_9ZeJ9kNMWn6JZFPAfyZkjsrHGSSjoFA	01.02-08.02 NQZ/7d	15	01.02-08.02 NIYET/7d	-	Astana	-	350	513.1	-	-	-	-	Double	HB	YES	SULEYMENOV	ABILKASIM	M	-	-	27.10.2030	-	-	1650	KUANBAEVA\tRAYA вместе	+7 702 441 9710	AKZHOL	family	/app/bull_project/bull_bot/tmp/uploads/bot_upload_1766837417053.png	new	2025-12-27 12:15:07.4676	\N
213	638331254	15iaUA4J5rgfAz6isS6BA07idUA9dXl-BW15FMw--7Vg	07.01-14.01 Ala-Jed/AA/7days	7	07.01-14.01 NIYET econom/7 days	Almaty	Almaty	Битрикс	980	510	Айдос ага	-	-	-	Quad	HB	-	AMIROVA	GULZIRA	F	29.05.1968	N18774264	-	680529402207	-	1400	Айдос аға	77714515417	Symbat	family	/app/bull_project/bull_bot/tmp/uploads/bot_upload_1767000202243.png	new	2025-12-29 09:36:10.235387	\N
137	8455844577	15iaUA4J5rgfAz6isS6BA07idUA9dXl-BW15FMw--7Vg	03.01-10.01 Ala-Jed/AA/7days	22	03.01-10.01NIYET com 7 days	Almaty	Almaty	Битрикс	195	514.5	NO	без авиа	-	без авиа	Double	HB	YES	KALIYEVA	AKKU	F	31.08.1987	N16249512	21.11.2033	870831400956	N0301	1020	Без авиа	+7 702 101 8777	Aqtolqyn	family	/app/bull_project/bull_bot/tmp/uploads/bot_upload_1766835154485.png	cancelled	2025-12-27 11:49:52.019175	\N
2	489877724	15iaUA4J5rgfAz6isS6BA07idUA9dXl-BW15FMw--7Vg	31.01-07.02 Ala-Med/AA/7days	8	31.01-07.02 HIKMA 7 days	Almaty	Almaty	-	2000 (1.000.000kzt) 	495	50	-	-	-	Triple	HB	-	MYNZHASSAROV	RAKHIMZHAN	M	14.09.1959	N16094956	23.10.2033	590914301464	-	2000	-	-	Nazerke	family	/app/bull_project/bull_bot/tmp/uploads/bot_upload_1766732975025.png	new	2025-12-26 07:12:48.72879	\N
3	489877724	15iaUA4J5rgfAz6isS6BA07idUA9dXl-BW15FMw--7Vg	31.01-07.02 Ala-Med/AA/7days	6	31.01-07.02 HIKMA 7 days	Almaty	Almaty	-	2000 (1.000.000kzt) 	495	50	-	-	-	Triple	HB	-	MYNZHASSAROVA	MARAL	F	06.01.1962	N15020990	28.12.2032	620106401802	-	2000	-	-	Nazerke	family	/app/bull_project/bull_bot/tmp/uploads/bot_upload_1766732985122.png	new	2025-12-26 07:12:48.941404	\N
1	489877724	15iaUA4J5rgfAz6isS6BA07idUA9dXl-BW15FMw--7Vg	31.01-07.02 Ala-Med/AA/7days	5	31.01-07.02 HIKMA 7 days	Almaty	Almaty	-	2000 (1.000.000kzt) 	495	50	-	-	-	Triple	HB	-	TEMIROVA	BAGLANKYZ	F	17.09.1951	N18763052	11.08.2035	510917401462	-	2000	-	-	Nazerke	family	/app/bull_project/bull_bot/tmp/uploads/bot_upload_1766732964992.png	new	2025-12-26 07:12:48.470816	\N
275	6911557357	15iaUA4J5rgfAz6isS6BA07idUA9dXl-BW15FMw--7Vg	28.01-04.02 Ala-Jed/AA/7days	78	28.01-04.02 NIYET /7 days	-	Almaty	-	1500	495	-	-	-	-	Double	HB	-	JAKUBAYEV	TUREBI	M	15.11.1979	Nl7817435	03.11.2034	791115300020	-	1550	-	87714444849 	Sagyndyk	family	/app/bull_project/bull_bot/tmp/uploads/bot_upload_1767093350410.png	new	2025-12-30 12:08:51.330547	["JAKUBAYEV TUREBI", "JAKUBAYEVA ARDAK"]
252	8471984589	15iaUA4J5rgfAz6isS6BA07idUA9dXl-BW15FMw--7Vg	16.01-23.01 NQZ/JED	14	16.01-23.01 NIYET econom /7 days	Astana	Astana	insta lid	350$	509.9	no	-	-	-	Quad	HB	-	MARGIZA	TORGOUTOVA	F	-	-	-	-	-	1350$	всех разместить в QDR номера	-	Zarina	separate	/app/bull_project/bull_bot/tmp/uploads/bot_upload_1767080784849.png	new	2025-12-30 07:53:56.423538	\N
285	6253997402	15iaUA4J5rgfAz6isS6BA07idUA9dXl-BW15FMw--7Vg	25.01-01.02 NQZ-MED/7days	69	25.01-01.02  IZI/7 days	-	Astana	-	100	495	-	-	-	-	Double	HB	-	TYUTYUKOVA	ZHULDYZAY	F	07.10.1986	N14035571	13.02.2032	861007401122	-	2750	-	-	AKZHOL	family	/app/bull_project/bull_bot/tmp/uploads/bot_upload_1767167261312.png	new	2025-12-31 07:49:56.510047	["TYUTYUKOVA ZHULDYZAY", "TYUTYUKOV ARMAN"]
286	6253997402	15iaUA4J5rgfAz6isS6BA07idUA9dXl-BW15FMw--7Vg	25.01-01.02 NQZ-MED/7days	70	25.01-01.02  IZI/7 days	-	Astana	-	100	495	-	-	-	-	Double	HB	-	TYUTYUKOV	ARMAN	M	29.12.1985	-	11.02.2022	851229350407	-	2750	-	-	AKZHOL	family	/app/bull_project/bull_bot/tmp/uploads/bot_upload_1767167293536.png	new	2025-12-31 07:49:56.846861	["TYUTYUKOVA ZHULDYZAY", "TYUTYUKOV ARMAN"]
455	6911557357	15iaUA4J5rgfAz6isS6BA07idUA9dXl-BW15FMw--7Vg	14.01-21.01 Ala-Jed/AA/7days	25	14.01-21.01 NIYET econom /7 days	-	Almaty	-	1400	495	-	-	-	-	Double	HB	-	MUKANOVA	YENGLIK	F	11.05.1998	N15166423	17.02.2023	980511400979	-	1400	-	87077157398	Sagyndyk	family	/app/bull_project/bull_bot/tmp/uploads/bot_upload_1767526380852.png	new	2026-01-04 11:35:55.725994	["RAMAZANOVA SALTANAT", "MUKANOVA YENGLIK"]
15	489877724	15iaUA4J5rgfAz6isS6BA07idUA9dXl-BW15FMw--7Vg	17.01-24.01 Ala-Med/AA/7days	37	17.01-24.01 HIKMA 7 days                                                                      Author’s Tour Nurlan imam	Shymkent	Almaty	lead	350	539.9	-	-	-	-	Triple	HB	-	SHERIMOV	ZHASSYLAK	M	06.05.1950	N12783973	17.12.2029	500506300184	-	2050	-	87075742829	Muslima	family	/app/bull_project/bull_bot/tmp/uploads/bot_upload_1766738613242.png	new	2025-12-26 08:46:38.293296	\N
310	8442162235	1r83RRUKrTQT_9ZeJ9kNMWn6JZFPAfyZkjsrHGSSjoFA	08.02-15.02 NQZ-MED/7d	79	08.02-15.02 IZI FAIRMONT /7d	-	Astana	-	100	495	-	AirAstana	-	AirAstana	Double	HB	-	SMAIL	BAUYRZHAN	M	19.05.1993	N15518436	11.06.2033	930519301806	-	2450	-	77077110304	Nursultan	family	/app/bull_project/bull_bot/tmp/uploads/bot_upload_1767181687946.pdf	new	2025-12-31 11:51:29.926353	["SMAIL BAUYRZHAN", "SMAIL JANARYS"]
37	8455844577	1r83RRUKrTQT_9ZeJ9kNMWn6JZFPAfyZkjsrHGSSjoFA	04.02-11.02 Ala-Med/7d	65	04.02-11.02 IZI Fairmont /7d	Almaty	Almaty	Битрикс	200	506.5	NO	NO	TOUR VISA	NO	Double	HB	YES	AMANZHOLOV	MURAT	M	09.02.1982	N15312288	03.04.2033	820209301203	N0402	4900	-	 +7 707 485 5847	Aqtolqyn	family	/app/bull_project/bull_bot/tmp/uploads/bot_upload_1766751869981.png	new	2025-12-26 12:31:03.257995	\N
24	8442162235	15iaUA4J5rgfAz6isS6BA07idUA9dXl-BW15FMw--7Vg	14.01-21.01 Ala-Med/AA/7days	17	14.01-21.01 HIKMA 7 days	Almaty	Almaty	База	350	509.5	-	AirAstana	UMRAH VISA	AirAstana	Triple	HB	YES	TURDIKULOV	SAYLAU TASTANOVICH	M	-	FA1590952	26.12.2030	-	-	1850	TURDYKULOV\tZHANDOS\nTURDYKULOVA\tKARIMA\nвместе с ними	+7 702 015 1717	Nursultan	family	/app/bull_project/bull_bot/tmp/uploads/bot_upload_1766743143897.png	new	2025-12-26 10:08:00.969831	\N
36	8455844577	1r83RRUKrTQT_9ZeJ9kNMWn6JZFPAfyZkjsrHGSSjoFA	04.02-11.02 Ala-Med/7d	64	04.02-11.02 IZI Fairmont /7d	Almaty	Almaty	Битрикс	200	506.5	NO	NO	TOUR VISA	NO	Double	HB	YES	SHALGIMBAYEVA	BOTA	F	20.08.1988	N11399394	30.07.2027	880820401321	N0402	4900	-	+7 776 208 1666	Aqtolqyn	family	/app/bull_project/bull_bot/tmp/uploads/bot_upload_1766751849001.png	new	2025-12-26 12:31:02.624164	\N
5	8348971315	15iaUA4J5rgfAz6isS6BA07idUA9dXl-BW15FMw--7Vg	07.01-14.01 Ala-Jed/AA/7days	7	07.01-14.01 NIYET econom/7 days	-	Almaty	-	980	495	-	-	-	-	Double	HB	-	BATYROVA	AKTOTY	F	18.02.1988	N13972622	21.11.2031	880218402476	-	1080	5000kazhy \n	-	Nazerke	family	/app/bull_project/bull_bot/tmp/uploads/bot_upload_1766733667618.png	new	2025-12-26 07:22:28.85334	\N
45	8455844577	15iaUA4J5rgfAz6isS6BA07idUA9dXl-BW15FMw--7Vg	21.01-28.01 Ala-Med/AA/7days	76	21.01-28.01 IZI FAIRMONT 7 days	Almaty	Almaty	База	100	500	100$ от руководства	NO	TOUR VISA	NO	Double	HB	YES	YUSSUPOVA	ZULFIYA	F	09.10.1988	N12948934	05.02.2030	881009400595	N2101	2450	-	+7 (747) 123-78-78	Aqtolqyn	family	/app/bull_project/bull_bot/tmp/uploads/bot_upload_1766753706963.png	new	2025-12-26 12:57:54.259226	\N
415	6911557357	15iaUA4J5rgfAz6isS6BA07idUA9dXl-BW15FMw--7Vg	31.01-07.02 Ala-Med/AA/7days	76	31.01-07.02 IZI FAIRMONT 7 days	-	Almaty	-	65	495	-	-	-	-	Triple	HB	-	ALIMOV	ILZATBEK	M	15.09.1963	N16040888	01.10.2033	630915300684	-	2150	-	+77014440092	Sagyndyk	separate	\N	new	2026-01-03 08:10:31.877841	["ALIMOV ILZATBEK"]
456	6911557357	1r83RRUKrTQT_9ZeJ9kNMWn6JZFPAfyZkjsrHGSSjoFA	04.02-11.02 Ala-Med/7d	68	04.02-11.02 IZI Fairmont /7d	-	Almaty	-	350	495	-	-	-	-	Double	HB	-	BELGIBAY	BAUYRZHAN	M	26.05.1996	-	14.11.2033	960526301087	-	2450	-	+77759920708	Sagyndyk	family	/app/bull_project/bull_bot/tmp/uploads/bot_upload_1767527607815.png	new	2026-01-04 11:58:30.735351	["BELGIBAY BAUYRZHAN", "KUDAIBERGEN ZHULDYZ"]
52	8413412150	15iaUA4J5rgfAz6isS6BA07idUA9dXl-BW15FMw--7Vg	17.01-24.01  Ala-Jed/AA/7days	46	17.01-24.01 NIYET econom /7 days	Other	Almaty	-	0	495	-	эконом	-	эконом	Quad	HB	-	AKHMEJANOV	KENES	M	-	-	-	-	-	1350	-	+7777 777 6717	.	family	/app/bull_project/bull_bot/tmp/uploads/bot_upload_1766753819887.png	new	2025-12-26 13:03:40.866108	\N
53	8455844577	15iaUA4J5rgfAz6isS6BA07idUA9dXl-BW15FMw--7Vg	21.01-28.01 Ala-Med/AA/7days	78	21.01-28.01 IZI FAIRMONT 7 days	Almaty	Almaty	База	100	500	100$ от руководства	NO	TOUR VISA	NO	Double	HB	YES	ZHANBOSSINOV	RAUAN	M	06.01.1989	N14173778	09.02.2032	890106300238	N2101	2350	-	+7 708 057 5757	Aqtolqyn	family	/app/bull_project/bull_bot/tmp/uploads/bot_upload_1766753911354.png	new	2025-12-26 13:11:12.975903	\N
139	7763611494	15iaUA4J5rgfAz6isS6BA07idUA9dXl-BW15FMw--7Vg	17.01-24.01 Ala-Med/AA/7days	38	17.01-24.01 HIKMA 7 days                                                                      Author’s Tour Nurlan imam	-	Almaty	-	350	495	-	-	-	-	Triple	HB	-	GNAZZUGAK	KUDAIBERGEN	M	28.09.1985	N15730601	18.07.2033	850928301199	-	2050	-	-	Hickmet	family	/app/bull_project/bull_bot/tmp/uploads/bot_upload_1766837662394.png	new	2025-12-27 12:17:03.804739	\N
55	7708752068	15iaUA4J5rgfAz6isS6BA07idUA9dXl-BW15FMw--7Vg	03.01-10.01 Ala-Jed/AA/7days	13	03.01-10.01NIYET com 7 days	-	Almaty	-	4650	495	-	-	-	-	Quad	HB	-	BAYAKHMETOV	DOSZHAN	M	17.09.1994	N14895949	06.11.2032	940917350852	-	6200	-	-	Hickmet Travel	family	/app/bull_project/bull_bot/tmp/uploads/bot_upload_1766757461427.png	new	2025-12-26 14:02:03.206152	\N
56	7708752068	15iaUA4J5rgfAz6isS6BA07idUA9dXl-BW15FMw--7Vg	03.01-10.01 Ala-Jed/AA/7days	14	03.01-10.01NIYET com 7 days	-	Almaty	-	4650	495	-	-	-	-	Quad	HB	-	ZHANGBYRBAY	ABDUROKHIM	M	24.08.2006	N18653459	01.09.2035	060824551216	-	6200	-	-	Hickmet Travel	family	/app/bull_project/bull_bot/tmp/uploads/bot_upload_1766757505680.png	new	2025-12-26 14:02:03.837717	\N
57	7708752068	15iaUA4J5rgfAz6isS6BA07idUA9dXl-BW15FMw--7Vg	03.01-10.01 Ala-Jed/AA/7days	15	03.01-10.01NIYET com 7 days	-	Almaty	-	4650	495	-	-	-	-	Quad	HB	-	MURZATAYEV	YERBOL	M	09.06.1981	N11633527	04.02.2028	810609350600	-	6200	-	-	Hickmet Travel	family	/app/bull_project/bull_bot/tmp/uploads/bot_upload_1766757526048.png	new	2025-12-26 14:02:04.473905	\N
44	8455844577	15iaUA4J5rgfAz6isS6BA07idUA9dXl-BW15FMw--7Vg	21.01-28.01 Ala-Med/AA/7days	64	21.01-28.01 IZI FAIRMONT 7 days	Almaty	Almaty	База	100	500	150$ от руководства	NO	TOUR VISA	NO	Triple	HB	YES	AKISHEV	RAKHAT	M	26.05.1988	N12809418	04.12.2029	880526301476	N2101	2100	Размещать вместе с AUKENOV KANAT,\nOSPANOV KAIRAT	+7 (705) 777-72-24 	Aqtolqyn	family	/app/bull_project/bull_bot/tmp/uploads/bot_upload_1766752929555.png	new	2025-12-26 12:54:34.336676	\N
58	7708752068	15iaUA4J5rgfAz6isS6BA07idUA9dXl-BW15FMw--7Vg	03.01-10.01 Ala-Jed/AA/7days	16	03.01-10.01NIYET com 7 days	-	Almaty	-	4650	495	-	-	-	-	Quad	HB	-	ZHANYRBAY	MUSTAFA	M	18.05.2014	N19284542	22.12.2030	140518502162	-	6200	-	-	Hickmet Travel	family	/app/bull_project/bull_bot/tmp/uploads/bot_upload_1766757558860.png	new	2025-12-26 14:02:04.778436	\N
214	638331254	15iaUA4J5rgfAz6isS6BA07idUA9dXl-BW15FMw--7Vg	07.01-14.01 Ala-Jed/AA/7days	8	07.01-14.01 NIYET econom/7 days	Almaty	Almaty	Битрикс	980	510	Айдос ага	-	-	-	Quad	HB	-	MUKHAMEJAN	RAMAZAN	M	-	N18774263	-	-	-	1400	Айдос аға	77714515417	Symbat	family	/app/bull_project/bull_bot/tmp/uploads/bot_upload_1767000218274.png	new	2025-12-29 09:36:10.870154	\N
141	6253997402	15iaUA4J5rgfAz6isS6BA07idUA9dXl-BW15FMw--7Vg	20.01-27.01 Ala-Jed/AA/7days	38	20.01-27.01 NIYET /7 days	Astana	Almaty	-	350$	514.5	-	-	-	-	Quad	HB	YES	ZHANBOLATOVA	ALAU	F	25.06.1983	N11772252	21.05.2028	830625401134	-	1550$	-	+7 775 286 4237	AKZHOL	family	/app/bull_project/bull_bot/tmp/uploads/bot_upload_1766840216931.png	new	2025-12-27 13:07:38.012974	\N
46	537576032	15iaUA4J5rgfAz6isS6BA07idUA9dXl-BW15FMw--7Vg	07.01-14.01 Ala-Jed/AA/7days	37	07.01-14.01 NIYET 7 days Courtyard	-	Almaty	-	98$	495	-	Эконом	TOUR VISA	Эконом	Quad	HB	-	TOKTAROV	MEDET	M	12.05.1988	11247722	31.05.2017	880512300858	-	1500$	Сперкубок, матч билеттерін өздері алған!	+7 701 666 8177	BEKTAY	family	/app/bull_project/bull_bot/tmp/uploads/bot_upload_1766753662238.png	new	2025-12-26 13:01:21.71613	\N
51	8413412150	15iaUA4J5rgfAz6isS6BA07idUA9dXl-BW15FMw--7Vg	17.01-24.01  Ala-Jed/AA/7days	45	17.01-24.01 NIYET econom /7 days	Other	Almaty	-	0	495	-	эконом	-	эконом	Quad	HB	-	AKHMEJANOV	RUSTEM	M	30.04.1990	N11629295	24.01.2028	900430300899	-	1350	-	+7777 777 6717	.	family	/app/bull_project/bull_bot/tmp/uploads/bot_upload_1766753808345.png	new	2025-12-26 13:03:40.579116	\N
140	7763611494	15iaUA4J5rgfAz6isS6BA07idUA9dXl-BW15FMw--7Vg	17.01-24.01 Ala-Med/AA/7days	39	17.01-24.01 HIKMA 7 days                                                                      Author’s Tour Nurlan imam	-	Almaty	-	350	495	-	-	-	-	Triple	HB	-	SHERIMOVA	YESSENKUL	F	05.12.1954	8550173	08.07.2035	541205401846	-	2050	-	-	Hickmet	family	/app/bull_project/bull_bot/tmp/uploads/bot_upload_1766837686031.png	new	2025-12-27 12:17:04.476301	\N
67	638331254	15iaUA4J5rgfAz6isS6BA07idUA9dXl-BW15FMw--7Vg	03.01-10.01 Ala-Jed/AA/7days	51	03.01-10.01 ALA-JED AA	NorthKazakhstan	Almaty	Битрикс	350	505.5	-50$	-	-	-	Double	HB	-	RAKHMANOVA	GULZHAN	F	20.04.1983	N17901210	07.01.2035	830420401090	-	1650	Супружеская пара, должна проживать вместе.	87022925199	Symbat	family	/app/bull_project/bull_bot/tmp/uploads/bot_upload_1766760884052.png	cancelled	2025-12-26 15:01:44.350686	\N
76	537576032	15iaUA4J5rgfAz6isS6BA07idUA9dXl-BW15FMw--7Vg	10.01- 17.01 Ala-Jed/7 d	51	10.01- 17.01 IZI Fairmont /7 days	-	Almaty	-	194	495	-	-	-	-	Double	HB	-	MAMADALIYEV	MURAT	M	25.05.1993	N15523168	01.06.2033	930525302193	-	2450	-	+77012862825	BEKTAY	family	/app/bull_project/bull_bot/tmp/uploads/bot_upload_1766828169617.png	new	2025-12-27 09:38:41.547993	\N
416	6911557357	15iaUA4J5rgfAz6isS6BA07idUA9dXl-BW15FMw--7Vg	31.01-07.02 Ala-Med/AA/7days	57	31.01-07.02 IZI FAIRMONT 7 days	-	Almaty	-	65	495	-	-	-	-	Triple	HB	-	ALIMOVA	RAKHIMEM	F	18.01.1968	N12809676	05.12.2029	680118402094	-	2150	-	+77014440092	Sagyndyk	separate	\N	new	2026-01-03 08:11:09.166531	["ALIMOVA RAKHIMEM"]
253	638331254	15iaUA4J5rgfAz6isS6BA07idUA9dXl-BW15FMw--7Vg	07.01-14.01 Ala-Jed/AA/7days	88	07.01-14.01 HIKMA	Almaty	Almaty	Битрикс	975	512	-	-	-	-	Double	HB	-	ZHYLYBAYEV	SUNKAR	M	13.07.1988	N16129085	14.11.2033	880713301175	-	3200	Суперкубок	77767010088	Symbat	separate	/app/bull_project/bull_bot/tmp/uploads/bot_upload_1767083119787.pdf	new	2025-12-30 08:26:40.065203	\N
70	6911557357	15iaUA4J5rgfAz6isS6BA07idUA9dXl-BW15FMw--7Vg	03.01-10.01 Ala-Jed/AA/7days	17	03.01-10.01NIYET com 7 days	Other	Almaty	Битрх	195	513.1	Нет	Туда и обратно	UMRAH VISA	Туда и обратно	Double	HB	YES	SULEIMANOV	ASSADBEK	M	08.06.2008	ПАСПОРТ	11.07.2027	080608552055	99999999	1700	Вместе SULEIMANOV SULEIMANOVA	+7 700 665 0643	Sagyndyk	family	/app/bull_project/bull_bot/tmp/uploads/bot_upload_1766777342342.png	new	2025-12-26 19:34:40.087096	\N
69	761594318	15iaUA4J5rgfAz6isS6BA07idUA9dXl-BW15FMw--7Vg	14.01-21.01 Ala-Jed/AA/7days	54	14.01-21.01 NIYET econom /7 days	-	Almaty	-	200	495	-	ECONOM	TOUR VISA	ECONOM	Quad	HB	-	ABDIGALIYEVA	ZHANALSYN	F	20.07.1957	N18768079	19.08.2035	570720400058	-	1350		+77012779937	lesbek.b	family	/app/bull_project/bull_bot/tmp/uploads/bot_upload_1766770263603.png	new	2025-12-26 17:33:57.193678	\N
66	638331254	15iaUA4J5rgfAz6isS6BA07idUA9dXl-BW15FMw--7Vg	03.01-10.01 Ala-Jed/AA/7days	50	03.01-10.01 ALA-JED AA	NorthKazakhstan	Almaty	Битрикс	350	505.5	-50$	-	-	-	Double	HB	-	YECHSHANOV	ASSYLBEK	M	16.08.1983	N11813077	10.09.2028	830816301265	-	1650	Супружеская пара, должна проживать вместе.	87022925199	Symbat	family	/app/bull_project/bull_bot/tmp/uploads/bot_upload_1766760862258.png	cancelled	2025-12-26 15:01:43.693467	\N
215	537576032	15iaUA4J5rgfAz6isS6BA07idUA9dXl-BW15FMw--7Vg	21.01-28.01 Ala-Med/AA/7days	84	21.01-28.01 IZI FAIRMONT 7 days	-	Almaty	-	2300$	495	-	My seat	-	My seat	Double	HB	-	ONALTAYEV	KOZBAY	M	05.05.1957	Nl1129142	11.01.2027	570505300260	-	2300$	Без хадж набора, цена согл с руководстом, запрос на My seat	+7 778 192 4715	BEKTAY	family	/app/bull_project/bull_bot/tmp/uploads/bot_upload_1767001024030.png	new	2025-12-29 09:39:46.786692	\N
418	844850166	1r83RRUKrTQT_9ZeJ9kNMWn6JZFPAfyZkjsrHGSSjoFA	01.02-08.02 NQZ/7d	56	01.02-08.02 HIKMA/7d	-	Astana	-	$2 050	495	-	-	-	-	Triple	HB	-	MUSTAFA	NAURYZBAY	M	-	-	-	-	-	$2 050	-	-	AYAZHAN	separate	\N	new	2026-01-03 08:50:20.2802	["MUSTAFA NAURYZBAY"]
71	6911557357	15iaUA4J5rgfAz6isS6BA07idUA9dXl-BW15FMw--7Vg	03.01-10.01 Ala-Jed/AA/7days	18	03.01-10.01NIYET com 7 days	Other	Almaty	Битрх	195	513.1	Нет	Туда и обратно	UMRAH VISA	Туда и обратно	Double	HB	YES	SULEIMANOVA	ZUKHRA	M	01.09.4976	-	28.04.2635	-	99999999	1700	Вместе SULEIMANOV SULEIMANOVA	+7 747 751 7503	Sagyndyk	family	/app/bull_project/bull_bot/tmp/uploads/bot_upload_1766777444937.png	new	2025-12-26 19:34:40.716879	\N
79	682201249	15iaUA4J5rgfAz6isS6BA07idUA9dXl-BW15FMw--7Vg	03.01-10.01 Ala-Jed/AA/7days	52	03.01-10.01 IZI fairmont 7 days	-	Almaty	-	2950	495	-	-	-	-	Double	HB	-	PLALOV	ALIBEK	M	19.10.1991	N18335344	25.05.2035	911019301103	-	2950	-	+77783038811	𝓫𝓪𝓴𝓸𝓷𝔂𝓪	family	/app/bull_project/bull_bot/tmp/uploads/bot_upload_1766828322868.png	new	2025-12-27 09:42:41.78257	\N
68	417871301	1r83RRUKrTQT_9ZeJ9kNMWn6JZFPAfyZkjsrHGSSjoFA	01.02-08.02 NQZ/7d	18	01.02-08.02 NIYET/7d	-	Astana	Bitrix	0	513,1	-	-	-	-	Double	HB	YES	KUANBAEVA	RAYA	F	03.05.1969	FA1415473	27.10.2050	-	-	1650	-	87024419710	Omirkhan	family	/app/bull_project/bull_bot/tmp/uploads/bot_upload_1766761199331.png	new	2025-12-26 15:37:53.243698	\N
146	6253997402	15iaUA4J5rgfAz6isS6BA07idUA9dXl-BW15FMw--7Vg	25.01-01.02 NQZ-MED/7days	65	25.01-01.02  IZI/7 days	Astana	Astana	-	350$	514.5	-	-	TOUR VISA	-	Double	HB	YES	YELEMESSOVA	ASSEL	F	16.08.1993	N11200512	23.08.2027	930816450469	-	2350$	-	+77025014000	AKZHOL	family	/app/bull_project/bull_bot/tmp/uploads/bot_upload_1766841436925.png	new	2025-12-27 13:20:38.949865	\N
77	682201249	15iaUA4J5rgfAz6isS6BA07idUA9dXl-BW15FMw--7Vg	03.01-10.01 Ala-Jed/AA/7days	50	03.01-10.01 IZI fairmont 7 days	-	Almaty	-	2950	495	-	-	-	-	Double	HB	-	KENZHEBAYEV	NURSULTAN	M	05.10.1993	N12053366	11.11.2028	931005301359	-	2950	-	+77783038811	𝓫𝓪𝓴𝓸𝓷𝔂𝓪	family	/app/bull_project/bull_bot/tmp/uploads/bot_upload_1766828264175.png	new	2025-12-27 09:42:41.239926	\N
311	8442162235	1r83RRUKrTQT_9ZeJ9kNMWn6JZFPAfyZkjsrHGSSjoFA	08.02-15.02 NQZ-MED/7d	80	08.02-15.02 IZI FAIRMONT /7d	-	Astana	-	100	495	-	AirAstana	-	AirAstana	Double	HB	-	SMAIL	JANARYS	M	-	-	-	-	-	2450	-	77077110304	Nursultan	family	\N	new	2025-12-31 11:51:30.250993	["SMAIL BAUYRZHAN", "SMAIL JANARYS"]
73	489877724	15iaUA4J5rgfAz6isS6BA07idUA9dXl-BW15FMw--7Vg	07.01-14.01 Ala-Med/AA/7days	64	07.01-14.01 IZI 7 days FAIRMONT	Almaty	Almaty	-	cумма оплаты: 4250$ kaspi/ 2.152.625kzt	506,5	-	BUSINESS CLASS	-	BUSINESS CLASS	Double	HB	-	BADAYEVA	NAZIRA	M	20.12.1953	-	-	-	-	2950	BUSINESS CLASS, разместить вместе с SHEDID ELINA в DBL	 +77752965413	AIYM	family	/app/bull_project/bull_bot/tmp/uploads/bot_upload_1766824937260.png	new	2025-12-27 08:44:06.973778	\N
65	417871301	15iaUA4J5rgfAz6isS6BA07idUA9dXl-BW15FMw--7Vg	10.01- 17.01 Ala-Jed/7 d	48	10.01- 17.01 IZI Fairmont /7 days	-	Almaty	Bitrix	100	506,5	-	-	-	-	Double	HB	YES	ZHUMABAYEVA	ULZHAN	F	05.10.2005	N16210280	12.12.2033	051005600543	-	2450	Комната с ABILAYEVA ALUA 	+7 705 706 5407	Omirkhan	family	/app/bull_project/bull_bot/tmp/uploads/bot_upload_1766755183004.png	new	2025-12-26 14:45:51.362568	\N
417	638331254	15iaUA4J5rgfAz6isS6BA07idUA9dXl-BW15FMw--7Vg	24.01-31.01 Ala-Med/AA/7days	87	24.01-31.01 IZI 7 days	Almaty	Almaty	Битрикс 	350	513	-	-	-	-	Triple	HB	-	BAYAN	KUANYSH	M	24.11.1992	N17938454	27.01.2035	921124301999	-	2150	-	77073155581	Symbat	separate	/app/bull_project/bull_bot/tmp/uploads/bot_upload_1767429556578.pdf	new	2026-01-03 08:40:31.861391	["BAYAN KUANYSH"]
78	682201249	15iaUA4J5rgfAz6isS6BA07idUA9dXl-BW15FMw--7Vg	03.01-10.01 Ala-Jed/AA/7days	51	03.01-10.01 IZI fairmont 7 days	-	Almaty	-	2950	495	-	-	-	-	Double	HB	-	YERIMBETOV	GAZIZ	M	27.08.1990	N14888727	08.11.2032	900827300768	-	2950	-	+77783038811	𝓫𝓪𝓴𝓸𝓷𝔂𝓪	family	/app/bull_project/bull_bot/tmp/uploads/bot_upload_1766828293075.png	new	2025-12-27 09:42:41.494418	\N
80	682201249	15iaUA4J5rgfAz6isS6BA07idUA9dXl-BW15FMw--7Vg	03.01-10.01 Ala-Jed/AA/7days	53	03.01-10.01 IZI fairmont 7 days	-	Almaty	-	2950	495	-	-	-	-	Double	HB	-	YELAMAN	ABYLAIKHAN	M	29.03.1994	N12653864	06.10.2029	940329300847	-	2950	-	+77783038811	𝓫𝓪𝓴𝓸𝓷𝔂𝓪	family	/app/bull_project/bull_bot/tmp/uploads/bot_upload_1766828336338.png	new	2025-12-27 09:42:42.036054	\N
419	537576032	15iaUA4J5rgfAz6isS6BA07idUA9dXl-BW15FMw--7Vg	07.01-14.01 Ala-Med/AA/7days	27	07.01-14.01 NIYET 7 days	-	Almaty	-	1700	495	-	-	-	-	Double	HB	-	ASSANOVA	ZHANNA	F	27.11.1977	N12503983	04.08.2029	771127402253	-	1700	-	+7 701 717 0877	Bektay 	separate	/app/bull_project/bull_bot/tmp/uploads/bot_upload_1767430580389.png	new	2026-01-03 08:57:44.938464	["ASSANOVA ZHANNA"]
420	537576032	15iaUA4J5rgfAz6isS6BA07idUA9dXl-BW15FMw--7Vg	07.01-14.01 Ala-Med/AA/7days	28	07.01-14.01 NIYET 7 days	-	Almaty	-	1700	495	-	-	-	-	Double	HB	-	KAIRGELDINA	BALNUR	F	26.03.1994	N13910109	-	940326401736	-	1700	-	‪+7 701 777 3769‬	Bektay 	separate	/app/bull_project/bull_bot/tmp/uploads/bot_upload_1767433202582.png	new	2026-01-03 09:41:19.791817	["KAIRGELDINA BALNUR"]
217	537576032	15iaUA4J5rgfAz6isS6BA07idUA9dXl-BW15FMw--7Vg	21.01-28.01 Ala-Med/AA/7days	86	21.01-28.01 IZI FAIRMONT 7 days	-	Almaty	-	2300$	495	-	-	-	-	Double	HB	-	MUKHAMEJANOVA	SALAMATKHAN	F	15.12.1955	N16491680	13.05.2034	551215401763	-	2300$	Без хадж набора, цена согл с руководстом\n	+7 778 651 3939	BEKTAY	family	/app/bull_project/bull_bot/tmp/uploads/bot_upload_1767001422597.png	new	2025-12-29 09:45:36.231009	\N
422	8442162235	15iaUA4J5rgfAz6isS6BA07idUA9dXl-BW15FMw--7Vg	30.01-06.02 Nqz-Jed/7d	29	30.01-06.02 NIYET econom 7 days	-	Astana	-	100	495	-	AirAstana	-	AirAstana	Double	HB	-	MENDYBAYEV	MARLEN	M	21.04.1989	N16301500	24.01.2034	890421350207	-	1450	-	77759897796	Nursultan	family	/app/bull_project/bull_bot/tmp/uploads/bot_upload_1767439115776.png	new	2026-01-03 11:21:31.710745	["MENDYBAYEVA MARINA", "MENDYBAYEV MARLEN"]
318	7763611494	15iaUA4J5rgfAz6isS6BA07idUA9dXl-BW15FMw--7Vg	17.01-24.01 Ala-Med/AA/7days	33	17.01-24.01 HIKMA 7 days                                                                      Author’s Tour Nurlan imam	Almaty	Almaty	база	2050	516,5	no	-	-	-	Triple	HB	YES	BURKITBAYEV	BAKYT	M	26.02.1963	N14932714	04.12.2032	630226301751	-	2050	-	-	Bayan	family	/app/bull_project/bull_bot/tmp/uploads/bot_upload_1767182782585.png	new	2025-12-31 12:09:07.603518	["BURKITBAYEV FARKHAT", "TUGELBAYEVA RAKHIMA", "BURKITBAYEV BAKYT"]
326	6253997402	15iaUA4J5rgfAz6isS6BA07idUA9dXl-BW15FMw--7Vg	28.01-04.02 Ala-Med/AA/7days	51	28.01-04.02 IZI FAIRMONT 7 days	-	Almaty	-	345.82	520.5	-	-	-	-	Double	HB	YES	NURLANBEKOVA	AINUR	F	05.08.1987	N14848138	26.09.2032	870805400042	-	2450	-	-	AKZHOL	family	/app/bull_project/bull_bot/tmp/uploads/bot_upload_1767197255421.png	new	2025-12-31 16:13:59.416831	["KHOJANAZAROV AZAMAT", "SMAILOV ADILZHAN", "KHOJANAZAROV ALISHER", "SANDYBAYEVA MENSULU", "TAURBAYEVA AIGANYM", "KHOJANAZAROV IBRAGIM", "NURLANBEKOVA AINUR", "MUSSINOVA GULZHAN", "SANDYBAYEV MARAT", "MUKANOVA ALTYNAY", "MUKANOV GABIT", "MUSSINOV YERMUKASH"]
327	6253997402	15iaUA4J5rgfAz6isS6BA07idUA9dXl-BW15FMw--7Vg	28.01-04.02 Ala-Med/AA/7days	52	28.01-04.02 IZI FAIRMONT 7 days	-	Almaty	-	345.82	520.5	-	-	-	-	Double	HB	YES	MUSSINOVA	GULZHAN	F	07.08.1961	N10527528	23.06.2026	610807400497	-	2450	-	-	AKZHOL	family	/app/bull_project/bull_bot/tmp/uploads/bot_upload_1767197277252.png	new	2025-12-31 16:13:59.742504	["KHOJANAZAROV AZAMAT", "SMAILOV ADILZHAN", "KHOJANAZAROV ALISHER", "SANDYBAYEVA MENSULU", "TAURBAYEVA AIGANYM", "KHOJANAZAROV IBRAGIM", "NURLANBEKOVA AINUR", "MUSSINOVA GULZHAN", "SANDYBAYEV MARAT", "MUKANOVA ALTYNAY", "MUKANOV GABIT", "MUSSINOV YERMUKASH"]
328	6253997402	15iaUA4J5rgfAz6isS6BA07idUA9dXl-BW15FMw--7Vg	28.01-04.02 Ala-Med/AA/7days	53	28.01-04.02 IZI FAIRMONT 7 days	-	Almaty	-	345.82	520.5	-	-	-	-	Double	HB	YES	SANDYBAYEV	MARAT	M	08.02.1965	N13298241	12.10.2030	650208300263	-	2450	-	-	AKZHOL	family	/app/bull_project/bull_bot/tmp/uploads/bot_upload_1767197333901.png	new	2025-12-31 16:14:00.072795	["KHOJANAZAROV AZAMAT", "SMAILOV ADILZHAN", "KHOJANAZAROV ALISHER", "SANDYBAYEVA MENSULU", "TAURBAYEVA AIGANYM", "KHOJANAZAROV IBRAGIM", "NURLANBEKOVA AINUR", "MUSSINOVA GULZHAN", "SANDYBAYEV MARAT", "MUKANOVA ALTYNAY", "MUKANOV GABIT", "MUSSINOV YERMUKASH"]
329	6253997402	15iaUA4J5rgfAz6isS6BA07idUA9dXl-BW15FMw--7Vg	28.01-04.02 Ala-Med/AA/7days	54	28.01-04.02 IZI FAIRMONT 7 days	-	Almaty	-	345.82	520.5	-	-	-	-	Double	HB	YES	MUKANOVA	ALTYNAY	F	25.12.1986	N13918782	15.08.2031	861225450542	-	2450	-	-	AKZHOL	family	/app/bull_project/bull_bot/tmp/uploads/bot_upload_1767197379325.png	new	2025-12-31 16:14:00.399361	["KHOJANAZAROV AZAMAT", "SMAILOV ADILZHAN", "KHOJANAZAROV ALISHER", "SANDYBAYEVA MENSULU", "TAURBAYEVA AIGANYM", "KHOJANAZAROV IBRAGIM", "NURLANBEKOVA AINUR", "MUSSINOVA GULZHAN", "SANDYBAYEV MARAT", "MUKANOVA ALTYNAY", "MUKANOV GABIT", "MUSSINOV YERMUKASH"]
330	6253997402	15iaUA4J5rgfAz6isS6BA07idUA9dXl-BW15FMw--7Vg	28.01-04.02 Ala-Med/AA/7days	55	28.01-04.02 IZI FAIRMONT 7 days	-	Almaty	-	345.82	520.5	-	-	-	-	Double	HB	YES	MUKANOV	GABIT	M	16.01.1986	N18439536	-	860116350987	-	2450	-	-	AKZHOL	family	/app/bull_project/bull_bot/tmp/uploads/bot_upload_1767197450179.png	new	2025-12-31 16:14:00.719529	["KHOJANAZAROV AZAMAT", "SMAILOV ADILZHAN", "KHOJANAZAROV ALISHER", "SANDYBAYEVA MENSULU", "TAURBAYEVA AIGANYM", "KHOJANAZAROV IBRAGIM", "NURLANBEKOVA AINUR", "MUSSINOVA GULZHAN", "SANDYBAYEV MARAT", "MUKANOVA ALTYNAY", "MUKANOV GABIT", "MUSSINOV YERMUKASH"]
332	6253997402	15iaUA4J5rgfAz6isS6BA07idUA9dXl-BW15FMw--7Vg	28.01-04.02 Ala-Med/AA/7days	57	28.01-04.02 IZI FAIRMONT 7 days	-	Almaty	-	192.12	495	-	-	-	-	Double	HB	-	SABITOVA	AIGERIM	F	06.05.1998	N13204195	04.10.2030	980506451292	-	2450	-	-	AKZHOL	family	/app/bull_project/bull_bot/tmp/uploads/bot_upload_1767197960923.png	new	2025-12-31 16:26:28.107822	["SABITOVA AIGERIM", "SMAILOVA AIDA", "DUISENBIYEV AIDOS"]
81	932021311	15iaUA4J5rgfAz6isS6BA07idUA9dXl-BW15FMw--7Vg	14.01-21.01 Ala-Jed/AA/7days	74	14.01-21.01 NIYET /7 days	-	Almaty	-	100	495	-	-	NO VISA	-	Quad	HB	-	AKKUL	NURDAULET	M	07.03.1995	N16450576	02.04.2034	950307301222	-	1550	-	-	ULZHAN	family	/app/bull_project/bull_bot/tmp/uploads/bot_upload_1767099649101.pdf	new	2025-12-27 10:09:32.812348	\N
421	8442162235	15iaUA4J5rgfAz6isS6BA07idUA9dXl-BW15FMw--7Vg	30.01-06.02 Nqz-Jed/7d	28	30.01-06.02 NIYET econom 7 days	-	Astana	-	100	495	-	AirAstana	-	AirAstana	Double	HB	-	MENDYBAYEVA	MARINA	F	01.05.1991	N14775201	18.10.2032	910501499059	-	1450	-	77759897796	Nursultan	family	/app/bull_project/bull_bot/tmp/uploads/bot_upload_1767439224943.pdf	new	2026-01-03 11:21:31.218731	["MENDYBAYEVA MARINA", "MENDYBAYEV MARLEN"]
147	6253997402	15iaUA4J5rgfAz6isS6BA07idUA9dXl-BW15FMw--7Vg	25.01-01.02 NQZ-MED/7days	66	25.01-01.02  IZI/7 days	Astana	Astana	-	350$	514.5	-	-	TOUR VISA	-	Double	HB	YES	YELEMESSOV	TOKHTAR	M	19.10.1991	N13804494	23.08.2031	911019350598	-	2350$	-	+77025014000	AKZHOL	family	/app/bull_project/bull_bot/tmp/uploads/bot_upload_1766841452697.png	new	2025-12-27 13:20:39.165813	\N
219	8348971315	15iaUA4J5rgfAz6isS6BA07idUA9dXl-BW15FMw--7Vg	07.01-14.01 Ala-Med/AA/7days	63	07.01-14.01 IZI 7 days FAIRMONT	Shymkent	Almaty	-	295,2	508,1	-	-	-	-	Double	HB	-	KOSSALIYEVA	ZHANAR	M	-	-	-	-	-	2950	размещение: \nАжибеков Құрымбай\nКосалиева Жанар;\n\nАлибеков Сагит\nКосалиева Гаухар.	-	Nazerke	family	 /app/bull_project/bull_bot/tmp/uploads/bot_upload_1767001258372.png	new	2025-12-29 10:18:41.060974	\N
209	8478709339	15iaUA4J5rgfAz6isS6BA07idUA9dXl-BW15FMw--7Vg	17.01-24.01 Ala-Med/AA/7days	27	17.01-24.01 HIKMA 7 days                                                                      Author’s Tour Nurlan imam	-	Almaty	-	1 960,3	495	-	-	-	-	Triple	HB	-	TURSUNBEKOVA	NURGUL	F	22.04.1966	-	-	660422401808	-	2150	-	87051475572 	Shyngys	family	/app/bull_project/bull_bot/tmp/uploads/bot_upload_1766995826817.png	new	2025-12-29 08:23:37.588136	\N
223	682201249	15iaUA4J5rgfAz6isS6BA07idUA9dXl-BW15FMw--7Vg	23.01-30.01 NQZ/MED/7d	20	23.01-30.01 NIYET econom	-	Astana	-	1400	495	-	-	-	-	Triple	HB	-	ZHUMANOV	ANUAR	M	28.06.1972	N15759070	23.07.2033	720628301528	-	1400	вместе SADVAKASSOVA GULMIRA\nIDRISSOVA NURBIKE	+7 701 554 4110	𝓫𝓪𝓴𝓸𝓷𝔂𝓪	family	/app/bull_project/bull_bot/tmp/uploads/bot_upload_1767010747309.png	new	2025-12-29 12:22:19.665731	\N
224	7763611494	15iaUA4J5rgfAz6isS6BA07idUA9dXl-BW15FMw--7Vg	03.01-10.01 Ala-Jed/AA/7days	54	03.01-10.01 ALA-JED AA	Almaty	Almaty	Лид	980	510,1	-	-	-	-	Quad	HB	YES	AKHMEDOV	DANIYAR	M	02.06.1977	-	28.06.2031	-	-	1550	-	-	Bayan	family	/app/bull_project/bull_bot/tmp/uploads/bot_upload_1767011986240.png	new	2025-12-29 12:42:03.709664	\N
225	7763611494	15iaUA4J5rgfAz6isS6BA07idUA9dXl-BW15FMw--7Vg	03.01-10.01 Ala-Jed/AA/7days	11	03.01-10.01NIYET com 7 days	Almaty	Almaty	лид 	980	510,1	-	-	-	-	Quad	HB	YES	AKHMEDOV	DANIYAR	M	02.06.1977	-	28.06.2031	-	-	1550	-	-	Bayan	family	/app/bull_project/bull_bot/tmp/uploads/bot_upload_1767011986240.png	new	2025-12-29 12:53:53.832916	\N
226	962578877	1dHYH2oJCFbHn6UAuRLzOBC9Ced5pazyFHcoNXoSHC0U	31.12-07.01 Ala-Med-Jed-Ala	61	31.12-07.01 IZI fairmont/7d	-	Almaty	-	2950	495	-	-	-	-	Double	HB	-	MADIYAR	OMIRBAY	M	-	-	-	-	-	2950	ВИЗА ЖОҚ ИЗИ ФЭЙРМОНТ 	+7 775 408 8886	Olzheke	family	\N	new	2025-12-29 13:34:21.821376	\N
232	6911557357	1LXBgCVtqyufEh_qfdxRxImEpMOlHAOTAEKgjHDgCSUA	25.03-01.04 ALA-MED	4	25.03-01.04 HIKMA/7d	-	Almaty	-	700	495	-	-	-	-	Double	HB	-	AKMURZIN	GAFUROLLA	M	20.07.1968	N12935143	24.05.2030	680720302249	-	1850	вместе  AKMURZIN AKKOZKIYEVA\nброн: 29.12.2025 350$+350$=700$ \nкурс 509.9$	+77058073367	Sagyndyk	family	/app/bull_project/bull_bot/tmp/uploads/bot_upload_1767016655638.png	new	2025-12-29 14:12:29.486956	\N
234	537576032	1dHYH2oJCFbHn6UAuRLzOBC9Ced5pazyFHcoNXoSHC0U	31.12-07.01 Ala-Med-Jed-Ala	61	31.12-07.01 IZI fairmont/7d	-	Almaty	-	0	495	-	-	-	-	Double	HB	-	TUSTIKBAYEV	ORYNBASSAR	M	15.03.1990	N14180572	21.02.2022	900315301257	-	2950	-	+7 778 020 6902	Bektay 	family	/app/bull_project/bull_bot/tmp/uploads/bot_upload_1767022732038.png	new	2025-12-29 15:42:11.577747	\N
235	6253997402	1r83RRUKrTQT_9ZeJ9kNMWn6JZFPAfyZkjsrHGSSjoFA	01.02-08.02 NQZ/7d	25	01.02-08.02 NIYET/7d	Astana	Astana	-	1600	509.9	50$ скидка куат устаздан	-	-	-	Double	HB	YES	SULEIMENOVA	BAKYT	F	01.01.1969	N16224762	04.01.2034	690101410699	-	1600	-	+7 776 044 5555	AKZHOL	family	/app/bull_project/bull_bot/tmp/uploads/bot_upload_1767023727488.png	new	2025-12-29 15:58:48.368556	\N
236	6253997402	1r83RRUKrTQT_9ZeJ9kNMWn6JZFPAfyZkjsrHGSSjoFA	08.02-15.02 NQZ-MED/7d	48	08.02-15.02 HIKMA /7d                                                                          Author’s Tour NURLAN imam	Astana	Astana	-	350	507.5	-	-	-	-	Double	HB	YES	NARMANBET	GALIYA	F	27.10.1958	N15092841	23.01.2033	581027450041	-	2150	экскурсия хира унгирине барып намаз оку	+7 708 425 6788	AKZHOL	family	/app/bull_project/bull_bot/tmp/uploads/bot_upload_1767024195845.png	new	2025-12-29 16:08:35.740101	\N
243	8455844577	15iaUA4J5rgfAz6isS6BA07idUA9dXl-BW15FMw--7Vg	14.01-21.01 Ala-Jed/AA/7days	69	14.01-21.01 NIYET /7 days	Almaty	Almaty	Битрикс	1550	511.7	NO	-	-	-	Quad	HB	YES	SHURENOVA	MAKHABBAT	F	25.11.1991	N14090327	26.12.2031	911125401740	N1401	1550	-	+7 702 251 9102	AKTOLKYN	separate	/app/bull_project/bull_bot/tmp/uploads/bot_upload_1767074875360.png	new	2025-12-30 06:11:06.607968	\N
254	638331254	1r83RRUKrTQT_9ZeJ9kNMWn6JZFPAfyZkjsrHGSSjoFA	04.02-11.02 Ala-Med/7d	66	04.02-11.02 IZI Fairmont /7d	-	Almaty	-	350	495	-	-	-	-	Double	HB	-	ZHYLYBAYEV	SUNKAR	M	13.07.1988	N16129085	14.11.2033	880713301175	-	2450	Муж и жена	77767010088	Symbat	family	/app/bull_project/bull_bot/tmp/uploads/bot_upload_1767083651309.pdf	new	2025-12-30 08:35:49.614981	\N
242	932021311	15iaUA4J5rgfAz6isS6BA07idUA9dXl-BW15FMw--7Vg	03.01-10.01 Ala-Med/AA/7days	65	03.01-10.01 IZI fairmont 7 days	-	Almaty	-	2600	495	-	-	-	-	Double	HB	-	KALDYBEKOVA	SAULE	F	04.04.1989	N16699236	03.05.2034	890404400086	-	2900	Возможно, уберем обратное авиа	-	ULZHAN	separate	/app/bull_project/bull_bot/tmp/uploads/bot_upload_1767070086593.png	new	2025-12-30 05:35:13.146284	\N
256	8348971315	1LXBgCVtqyufEh_qfdxRxImEpMOlHAOTAEKgjHDgCSUA	07.03-21.03.2026 Ala-Jed	20	07.03-21.03 PARK REGIS	-	Almaty	-	1900	495	-	-	TOUR VISA	-	Double	RO	-	KOZYBAKOV	TAUIRZHAN	M	15.08.1962	N11161713	26.02.2027	620815300258	-	1900	-	-	Nazerke 	family	/app/bull_project/bull_bot/tmp/uploads/bot_upload_1767080393989.png	new	2025-12-30 09:05:18.107548	\N
257	8348971315	1LXBgCVtqyufEh_qfdxRxImEpMOlHAOTAEKgjHDgCSUA	07.03-21.03.2026 Ala-Jed	21	07.03-21.03 PARK REGIS	-	Almaty	-	1900	495	-	-	TOUR VISA	-	Double	RO	-	NURGALIYEVA	GULMIRA	F	04.10.1967	N13783236	08.06.2031	671004401295	-	1900	-	-	Nazerke 	family	/app/bull_project/bull_bot/tmp/uploads/bot_upload_1767080408891.png	new	2025-12-30 09:05:19.090499	\N
74	489877724	15iaUA4J5rgfAz6isS6BA07idUA9dXl-BW15FMw--7Vg	07.01-14.01 Ala-Med/AA/7days	65	07.01-14.01 IZI 7 days FAIRMONT	Almaty	Almaty	-	Cумма оплаты: 4250$ kaspi/ 2.152.625kzt	506,5	-	-	-	-	Double	HB	-	SHEDID	ELINA	F	14.05.1990	N14858287	12.10.2032	-	-	2300$	BUSINESS CLASS, разместить вместе с SHEDID ELINA в DBL	+77714499999	AIYM	family	/app/bull_project/bull_bot/tmp/uploads/bot_upload_1766825442849.png	new	2025-12-27 08:53:52.684659	\N
218	537576032	15iaUA4J5rgfAz6isS6BA07idUA9dXl-BW15FMw--7Vg	21.01-28.01 Ala-Med/AA/7days	87	21.01-28.01 IZI FAIRMONT 7 days	-	Almaty	-	2300$	495	-	-	-	-	Double	HB	-	KHAMRAKULOVA	MARKHABAT	F	09.04.1950	N16484125	28.04.2034	500409401240	-	2300$	Без хадж набора, цена согл с руководстом\n	+7 778 651 3939	BEKTAY	family	/app/bull_project/bull_bot/tmp/uploads/bot_upload_1767001452597.png	new	2025-12-29 09:45:36.516027	\N
423	8455844577	15iaUA4J5rgfAz6isS6BA07idUA9dXl-BW15FMw--7Vg	21.01-28.01 Ala-Med/AA/7days	48	21.01-28.01 HIKMA 7 days	Almaty	Almaty	Битрикс	1930	513.7	120$ скидка от рк и без хадж набора	-	-	-	Triple	HB	YES	ZHILKIBAYEV	BEKBULAT	M	19.11.1986	N15413084	02.05.2033	861119301521	2101b	1930	Без хадж набора и скидка 70$ от рк	+7 778 858 3120	AKTOLKYN	separate	/app/bull_project/bull_bot/tmp/uploads/bot_upload_1767444483496.png	new	2026-01-03 12:50:36.445046	["ZHILKIBAYEV BEKBULAT"]
160	7763611494	15iaUA4J5rgfAz6isS6BA07idUA9dXl-BW15FMw--7Vg	21.01-28.01 Ala-Med/AA/7days	65	21.01-28.01 IZI FAIRMONT 7 days	-	Almaty	Сарафанка	97	5145	-	-	-	-	Double	HB	YES	MAUTKANOV	RINAT	M	15.01.1986	N12193853	26.02.2029	860115301834	-	2450	-	-	BAYAN	separate	/app/bull_project/bull_bot/tmp/uploads/bot_upload_1766913409697.png	new	2025-12-28 09:20:18.245038	\N
166	8442162235	15iaUA4J5rgfAz6isS6BA07idUA9dXl-BW15FMw--7Vg	17.01-24.01 Ala-Med/AA/7days	23	17.01-24.01 HIKMA 7 days                                                                      Author’s Tour Nurlan imam	-	Almaty	-	350	495	-	AirAstana	-	AirAstana	Double	HB	-	ILYASSOVA	KURALAY	F	13.01.1979	N15798130	31.07.2023	790113403711	-	2300	-	77789562229	Nursultan	family	/app/bull_project/bull_bot/tmp/uploads/bot_upload_1766934683379.png	new	2025-12-28 15:13:43.541145	\N
424	844850166	15iaUA4J5rgfAz6isS6BA07idUA9dXl-BW15FMw--7Vg	16.01-23.01 NQZ/JED	24	16.01-23.01 NIYET econom /7 days	-	Astana	-	$ 350	495	-	-	TOUR VISA	-	Quad	HB	-	TAUKENOVA	SHUGA	F	24.05.1964	N14019035	21.12.2031	640524450272	-	$1250	-	+7 701 308 3537	AYAZHAN	separate	/app/bull_project/bull_bot/tmp/uploads/bot_upload_1767446779536.pdf	new	2026-01-03 13:31:46.774869	["TAUKENOVA SHUGA"]
148	6253997402	15iaUA4J5rgfAz6isS6BA07idUA9dXl-BW15FMw--7Vg	25.01-01.02 NQZ-MED/7days	64	25.01-01.02  IZI/7 days	-	Astana	-	350$	495	-	-	-	-	Double	HB	-	SMAGUL	SYMBAT	F	09.02.1994	N16412831	02.04.2034	940209401363	-	2450$	GALINURULY MUKHAMMED Child 910$ 	+7 702 589 3391	AKZHOL	family	/app/bull_project/bull_bot/tmp/uploads/bot_upload_1766842512700.png	new	2025-12-27 13:38:27.602754	\N
457	6911557357	1r83RRUKrTQT_9ZeJ9kNMWn6JZFPAfyZkjsrHGSSjoFA	04.02-11.02 Ala-Med/7d	69	04.02-11.02 IZI Fairmont /7d	-	Almaty	-	350	495	-	-	-	-	Double	HB	-	KUDAIBERGEN	ZHULDYZ	F	11.04.1997	-	14.11.2033	970411401466	-	2450	-	+77475155004	Sagyndyk	family	/app/bull_project/bull_bot/tmp/uploads/bot_upload_1767527658840.png	new	2026-01-04 11:58:31.112958	["BELGIBAY BAUYRZHAN", "KUDAIBERGEN ZHULDYZ"]
255	638331254	1r83RRUKrTQT_9ZeJ9kNMWn6JZFPAfyZkjsrHGSSjoFA	04.02-11.02 Ala-Med/7d	67	04.02-11.02 IZI Fairmont /7d	-	Almaty	-	350	495	-	-	-	-	Double	HB	-	AMANTAYEVA	AYAZHAN	F	29.04.2000	N16138306	26.11.2033	000429600983	-	2450	Муж и жена	77055024880	Symbat	family	/app/bull_project/bull_bot/tmp/uploads/bot_upload_1767083670790.pdf	new	2025-12-30 08:35:51.352177	\N
157	8471984589	15iaUA4J5rgfAz6isS6BA07idUA9dXl-BW15FMw--7Vg	21.01-28.01 Ala-Med/AA/7days	83	21.01-28.01 IZI FAIRMONT 7 days	-	Almaty	-	200	495	-	Бизнес класс 	-	Бизнес класс 	Double	HB	-	AMIRALINOV	FARKHAT	M	11.05.1982	N13960042	28.10.2031	820511300504	-	2450	Запрос на бизнес класс.	+77057716171	Hickmet	family	/app/bull_project/bull_bot/tmp/uploads/bot_upload_1766908757630.png	new	2025-12-28 08:04:55.155085	\N
158	6911557357	15iaUA4J5rgfAz6isS6BA07idUA9dXl-BW15FMw--7Vg	20.01-27.01 Ala-Jed/AA/7days	50	20.01-27.01 NIYET /7 days	Zhambyl	Almaty	bitrx	150	514.5	no	-	-	-	Double	HB	YES	SAGYNDYKOV	RUSTEMBEK	M	-	-	-	-	4444	1650	вместе SAGYNDYKOV, сюрприз жасап жатыр,группаға қосарда Сағындық менеджердан сұраңыздар	+7 707 280 019	Sagyndyk	family	 /app/bull_project/bull_bot/tmp/uploads/bot_upload_1766908959404.png	new	2025-12-28 08:15:59.441561	\N
159	6911557357	15iaUA4J5rgfAz6isS6BA07idUA9dXl-BW15FMw--7Vg	20.01-27.01 Ala-Jed/AA/7days	51	20.01-27.01 NIYET /7 days	Zhambyl	Almaty	bitrx	150	514.5	no	-	-	-	Double	HB	YES	SAGYNDYKOV	KAZBEK	M	-	-	-	-	4444	1650	вместе SAGYNDYKOV, сюрприз жасап жатыр,группаға қосарда Сағындық менеджердан сұраңыздар	+7 777 117 7662	Sagyndyk	family	 /app/bull_project/bull_bot/tmp/uploads/bot_upload_1766909043625.png	new	2025-12-28 08:15:59.718321	\N
156	8471984589	15iaUA4J5rgfAz6isS6BA07idUA9dXl-BW15FMw--7Vg	21.01-28.01 Ala-Med/AA/7days	82	21.01-28.01 IZI FAIRMONT 7 days	-	Almaty	-	200	495	-	Бизнес класс 	-	Бизнес класс 	Double	HB	-	AMIRALINOVA	INDIRA	F	08.04.1984	-	04.11.2034	840408400148	-	2450	Запрос на бизнес класс.	+77051390105	Hickmet	family	 /app/bull_project/bull_bot/tmp/uploads/bot_upload_1766908749688.png	new	2025-12-28 08:04:54.872579	\N
164	7763611494	15iaUA4J5rgfAz6isS6BA07idUA9dXl-BW15FMw--7Vg	17.01-24.01 Ala-Med/AA/7days	19	17.01-24.01 HIKMA 7 days                                                                      Author’s Tour Nurlan imam	-	Almaty	-	97	495	-	-	-	-	Double	HB	-	YESSIMKHANOVA	AISHAKHON	F	21.09.1972	N11395413	23.07.2027	720921402426	-	2300	-	+77021395593	Bayan	family	/app/bull_project/bull_bot/tmp/uploads/bot_upload_1766923490866.png	new	2025-12-28 12:07:45.066255	\N
168	682201249	15iaUA4J5rgfAz6isS6BA07idUA9dXl-BW15FMw--7Vg	17.01-24.01  Ala-Jed/AA/7days	81	17.01-24.01 NIYET /7 days	-	Almaty	-	1550	495	-	-	-	-	Double	HB	-	ZHIGITOV	UZAKBAY	M	21.07.1993	N14854296	05.10.2032	930721301993	-	1550	 RAKHYMBERDIYEV DAUREN own visa	‪+7 701 507 8220‬	𝓫𝓪𝓴𝓸𝓷𝔂𝓪	family	/app/bull_project/bull_bot/tmp/uploads/bot_upload_1766939293661.png	new	2025-12-28 16:32:46.666154	\N
220	8348971315	15iaUA4J5rgfAz6isS6BA07idUA9dXl-BW15FMw--7Vg	07.01-14.01 Ala-Med/AA/7days	64	07.01-14.01 IZI 7 days FAIRMONT	Shymkent	Almaty	-	295,2	508,1	-	-	-	-	Double	HB	-	KOSSALIYEVA	GAUKHAR	M	-	-	-	-	-	2950	размещение: \nАжибеков Құрымбай\nКосалиева Жанар;\n\nАлибеков Сагит\nКосалиева Гаухар.	-	Nazerke	family	NULL	new	2025-12-29 10:18:41.692229	\N
233	6911557357	1LXBgCVtqyufEh_qfdxRxImEpMOlHAOTAEKgjHDgCSUA	25.03-01.04 ALA-MED	5	25.03-01.04 HIKMA/7d	-	Almaty	-	700	495	-	-	-	-	Double	HB	-	AKKOZKIYEVA	GULNAZIYA	F	16.12.1968	N12935142	24.05.2030	681216401428	-	1850	вместе  AKMURZIN AKKOZKIYEVA\nброн: 29.12.2025 350$+350$=700$ \nкурс 509.9$	+77058073367	Sagyndyk	family	/app/bull_project/bull_bot/tmp/uploads/bot_upload_1767016672085.png	new	2025-12-29 14:12:29.754239	\N
258	932021311	15iaUA4J5rgfAz6isS6BA07idUA9dXl-BW15FMw--7Vg	14.01-21.01 Ala-Med/AA/7days	27	14.01-21.01 HIKMA 7 days	-	Almaty	-	500	495	-	Без обратки	-	Без обратки	Triple	HB	-	SYZDYKOV	DOSSYMZHAN	M	14.08.1991	N13075652	17.09.2030	910814301201	-	1850	АВИА ТУДА ПО СИСТЕМЕ КУПИЛИ	‪+7 776 000 0100‬	ULZHAN	separate	/app/bull_project/bull_bot/tmp/uploads/bot_upload_1767086808105.pdf	new	2025-12-30 09:27:25.185601	\N
260	932021311	15iaUA4J5rgfAz6isS6BA07idUA9dXl-BW15FMw--7Vg	07.01-14.01 Ala-Jed/AA/7days	18	07.01-14.01 NIYET econom/7 days	-	Almaty	-	1400	495	-	-	-	-	Quad	HB	-	ZAMIROV	KAMILZHAN	M	19.11.1998	N13406446	03.12.2030	981119300924	-	1400	-	87015413252	ULZHAN	separate	/app/bull_project/bull_bot/tmp/uploads/bot_upload_1767089312916.png	new	2025-12-30 10:09:37.59213	\N
98	537576032	15iaUA4J5rgfAz6isS6BA07idUA9dXl-BW15FMw--7Vg	23.01-30.01 NQZ/MED/7d	18	23.01-30.01 NIYET econom	-	Astana	-	98$	495	-	-	TOUR VISA	-	Triple	HB	-	KARBAY	OMARKHAN	M	05.12.2014	N15694370	12.07.2033	141205501756	-	1300$	-	77054770832	BEKTAY	family	/app/bull_project/bull_bot/tmp/uploads/bot_upload_1766833602013.png	new	2025-12-27 11:08:56.731121	\N
149	6253997402	15iaUA4J5rgfAz6isS6BA07idUA9dXl-BW15FMw--7Vg	25.01-01.02 NQZ-MED/7days	65	25.01-01.02  IZI/7 days	-	Astana	-	350$	495	-	-	-	-	Double	HB	-	GALINURULY	MUKHAMMED	M	-	-	-	-	-	2450$	GALINURULY MUKHAMMED Child 910$ 	-	AKZHOL	family	/app/bull_project/bull_bot/tmp/uploads/bot_upload_1766842538139.png	new	2025-12-27 13:38:27.888198	\N
259	537576032	15iaUA4J5rgfAz6isS6BA07idUA9dXl-BW15FMw--7Vg	21.01-28.01 Ala-Med/AA/7days	85	21.01-28.01 IZI FAIRMONT 7 days	-	Almaty	-	2200$	495	-	-	-	-	Triple	HB	-	ABDULAYEVA	MAVZHUDA	F	19.05.1961	N14626908	-	610519402646	-	2200$	-	+7 778 651 3939	BEKTAY	separate	/app/bull_project/bull_bot/tmp/uploads/bot_upload_1767087479617.png	new	2025-12-30 09:40:56.033935	\N
162	7763611494	15iaUA4J5rgfAz6isS6BA07idUA9dXl-BW15FMw--7Vg	28.01-04.02 Ala-Jed/AA/7days	76	28.01-04.02 NIYET /7 days	-	Almaty	-	48,5	495	-	-	-	-	Double	HB	-	ZHALMAGAMBETOVA	GULZHAN	F	24.06.1972	N11230329	24.04.2027	720624401532	-	1650	-	-	BAYAN	family	/app/bull_project/bull_bot/tmp/uploads/bot_upload_1766914194868.png	new	2025-12-28 09:34:08.688982	\N
165	7763611494	15iaUA4J5rgfAz6isS6BA07idUA9dXl-BW15FMw--7Vg	17.01-24.01 Ala-Med/AA/7days	20	17.01-24.01 HIKMA 7 days                                                                      Author’s Tour Nurlan imam	-	Almaty	-	97	495	-	-	-	-	Double	HB	-	YESSIMKHANOV	RUSLAN	M	29.12.1968	N15670570	11.07.2023	681229301422	-	2300	-	+77023532424	Bayan	family	/app/bull_project/bull_bot/tmp/uploads/bot_upload_1766923517364.png	new	2025-12-28 12:07:45.359699	\N
167	8442162235	15iaUA4J5rgfAz6isS6BA07idUA9dXl-BW15FMw--7Vg	17.01-24.01 Ala-Med/AA/7days	24	17.01-24.01 HIKMA 7 days                                                                      Author’s Tour Nurlan imam	-	Almaty	-	350	495	-	AirAstana	-	AirAstana	Double	HB	-	SANDYBEKOV	BEKBERGEN	M	10.06.1978	N11345555	05.12.2027	780610350330	-	2300	-	77789562229	Nursultan	family	/app/bull_project/bull_bot/tmp/uploads/bot_upload_1766934712587.png	new	2025-12-28 15:13:44.215775	\N
169	682201249	15iaUA4J5rgfAz6isS6BA07idUA9dXl-BW15FMw--7Vg	17.01-24.01  Ala-Jed/AA/7days	82	17.01-24.01 NIYET /7 days	-	Almaty	-	1550	495	-	-	-	-	Double	HB	-	KAMALOVA	BALZHAN	F	11.05.1998	N13140786	07.10.2030	980511400285	-	1550	 RAKHYMBERDIYEV DAUREN own visa	‪+7 701 507 8220‬	𝓫𝓪𝓴𝓸𝓷𝔂𝓪	family	/app/bull_project/bull_bot/tmp/uploads/bot_upload_1766939335918.png	new	2025-12-28 16:32:47.306591	\N
261	1116499112	1r83RRUKrTQT_9ZeJ9kNMWn6JZFPAfyZkjsrHGSSjoFA	04.02-11.02 Ala-Jed-Med-Ala/7d	10	04.02-11.02 NIYET econom /7d	Almaty	Almaty	Baza	49	512,7	20$	NO	-	NO	Quad	HB	-	INSEBAYEVA	MUNIRA	F	22.02.2006	N187458956	19.10.2035	060222650261	-	1330	Сандра паспорт скоро отправлю 	87083013563	PERIZAT 	separate	/app/bull_project/bull_bot/tmp/uploads/bot_upload_1767089969153.pdf	new	2025-12-30 10:21:36.525591	\N
221	8348971315	15iaUA4J5rgfAz6isS6BA07idUA9dXl-BW15FMw--7Vg	07.01-14.01 Ala-Med/AA/7days	67	07.01-14.01 IZI 7 days FAIRMONT	Shymkent	Almaty	-	295,2	508,1	-	-	-	-	Double	HB	-	ALIBEKOV	SAGIT	M	-	-	-	-	-	2950	размещение: \nАжибеков Құрымбай\nКосалиева Жанар;\n\nАлибеков Сагит\nКосалиева Гаухар.	-	Nazerke	family	 /app/bull_project/bull_bot/tmp/uploads/bot_upload_1767001590817.png	new	2025-12-29 10:18:42.163299	\N
188	8442162235	15iaUA4J5rgfAz6isS6BA07idUA9dXl-BW15FMw--7Vg	07.01-14.01 Ala-Jed/AA/7days	88	07.01-14.01 HIKMA	-	Almaty	-	0	495	-	+7 777 777 4770	UMRAH VISA	+7 777 777 4770	Double	HB	-	ILYASSOV	ALGIS	M	05.02.1989	N17142417	06.08.2034	890205300385	-	3300	Филиал Семей будет оплачивать	-	Nursultan	family	/app/bull_project/bull_bot/tmp/uploads/bot_upload_1766989012702.png	new	2025-12-29 06:19:26.275412	\N
230	844850166	15iaUA4J5rgfAz6isS6BA07idUA9dXl-BW15FMw--7Vg	17.01-24.01 Ala-Med/AA/7days	28	17.01-24.01 HIKMA 7 days                                                                      Author’s Tour Nurlan imam	Almaty	Almaty	bitrix	785	514.5	-50$ от руководства	-	-	-	Triple	HB	YES	YEGDIRBAYEVA	GULMIRA	F	09.10.1967	N11860508	17.05.2018	671009402369	N1701	$2100	-	-	AYAZHAN	family	/app/bull_project/bull_bot/tmp/uploads/bot_upload_1767015656518.png	new	2025-12-29 13:48:58.709629	\N
246	8348971315	15iaUA4J5rgfAz6isS6BA07idUA9dXl-BW15FMw--7Vg	07.01-14.01 Ala-Jed/AA/7days	59	07.01-14.01 NIYET 7 days Courtyard	-	Almaty	-	950	495	-	-	-	-	Double	HB	-	RUZBAKIYEV	RAKHIM	M	07.02.1977	N17089348	02.05.2034	770207301657	-	1600	-	-	Nazerke	family	/app/bull_project/bull_bot/tmp/uploads/bot_upload_1767071586985.png	new	2025-12-30 07:39:00.392747	\N
247	8348971315	15iaUA4J5rgfAz6isS6BA07idUA9dXl-BW15FMw--7Vg	07.01-14.01 Ala-Jed/AA/7days	60	07.01-14.01 NIYET 7 days Courtyard	-	Almaty	-	950	495	-	-	-	-	Double	HB	-	RUZBAKIYEVA	ZULFIYA	F	30.01.1983	N13286667	26.07.2030	830130400393	-	1600	-	-	Nazerke	family	/app/bull_project/bull_bot/tmp/uploads/bot_upload_1767071612457.png	new	2025-12-30 07:39:01.352898	\N
295	1116499112	15iaUA4J5rgfAz6isS6BA07idUA9dXl-BW15FMw--7Vg	07.01-14.01 Ala-Med/AA/7days	69	07.01-14.01 IZI 7 days FAIRMONT	Almaty	Almaty	Bitrix	24	518,5	-	-	-	-	Double	HB	-	NASSIBOV	AZIZ	M	15.10.1995	N12388427	11.04.2029	951015300051	-	2950	Русскоязычный гид	87018084444	PERIZAT 	family	/app/bull_project/bull_bot/tmp/uploads/bot_upload_1767177086997.png	new	2025-12-31 11:00:33.992634	["NASSIBOV AZIZ", "NASSIBOVA GULESSER", "AKHMEDOV RUSTAM", "AKHMEDOVA GULCHACHAK"]
307	8107860854	15iaUA4J5rgfAz6isS6BA07idUA9dXl-BW15FMw--7Vg	07.01-14.01 Ala-Med/AA/7days	51	07.01-14.01 HIKMA 7 days	Almaty	Almaty	сарафанка	2100$	519.5	100$	-	-	-	Triple	HB	YES	GABASSOV	AZAMAT	M	09.01.1983	N18998833	07.12.2035	830109301767	-	2100$	дать ПОЛНОЦЕННЫЙ TRIPLE НОМЕР, разместить всех вместе  AISA ABYLAY,GABASSOV AZAMAT,AISA ISSATAY	+7 700 777 7217	AIYM	family	/app/bull_project/bull_bot/tmp/uploads/bot_upload_1767179742987.png	new	2025-12-31 11:40:47.810052	["AISA ABYLAY", "AISA ISSATAY", "GABASSOV AZAMAT"]
312	8442162235	15iaUA4J5rgfAz6isS6BA07idUA9dXl-BW15FMw--7Vg	07.01-14.01 Ala-Jed/AA/7days	69	07.01-14.01 NIYET 7 days Courtyard	-	Almaty	-	100	495	-	AirAstana	-	AirAstana	Quad	HB	-	ZEKENOV	ANUAR	M	19.10.1994	N14917305	01.12.2032	941019350107	-	1600	-	+7 778 385 4042	Nursultan	separate	/app/bull_project/bull_bot/tmp/uploads/bot_upload_1767182248193.pdf	new	2025-12-31 11:58:21.381963	["ZEKENOV ANUAR"]
189	932021311	15iaUA4J5rgfAz6isS6BA07idUA9dXl-BW15FMw--7Vg	24.01-31.01 Ala-Med/AA/7days	83	24.01-31.01 IZI 7 days	-	Almaty	-	100	495	-	-	-	-	Triple	HB	-	JUSSUPBAYEV	BAGLAN	M	12.02.1990	-	28.10.2034	900212300299	-	2150	ЕСТЬ INFANT\n	-	ULZHAN	family	/app/bull_project/bull_bot/tmp/uploads/bot_upload_1766989746284.png	new	2025-12-29 06:30:32.650363	\N
161	7763611494	15iaUA4J5rgfAz6isS6BA07idUA9dXl-BW15FMw--7Vg	21.01-28.01 Ala-Med/AA/7days	66	21.01-28.01 IZI FAIRMONT 7 days	-	Almaty	Сарафанка	97	5145	-	-	-	Business class 	Double	HB	YES	MUSSAYEV	MARAT	M	29.08.1987	N15483330	24.05.2033	870829301759	-	2450	Индивидуальный гид и личный трансфер, 	-	BAYAN	separate	/app/bull_project/bull_bot/tmp/uploads/bot_upload_1766913438092.png	new	2025-12-28 09:20:18.56876	\N
163	7763611494	15iaUA4J5rgfAz6isS6BA07idUA9dXl-BW15FMw--7Vg	28.01-04.02 Ala-Jed/AA/7days	77	28.01-04.02 NIYET /7 days	-	Almaty	-	48,5	495	-	-	-	-	Double	HB	-	KEIKISHEV	ADILBEK	M	30.01.1966	N17776748	-	660130302208	-	1650	-	-	BAYAN	family	/app/bull_project/bull_bot/tmp/uploads/bot_upload_1766914254430.png	new	2025-12-28 09:34:08.919127	\N
170	682201249	15iaUA4J5rgfAz6isS6BA07idUA9dXl-BW15FMw--7Vg	17.01-24.01  Ala-Jed/AA/7days	83	17.01-24.01 NIYET /7 days	-	Almaty	-	1550	495	-	-	-	-	Double	HB	-	UTEPKALIYEVA	AIGERIM	F	02.08.1998	N14431173	12.05.2032	980802401334	-	1550	 RAKHYMBERDIYEV DAUREN own visa	‪+7 707 934 0966‬	𝓫𝓪𝓴𝓸𝓷𝔂𝓪	family	/app/bull_project/bull_bot/tmp/uploads/bot_upload_1766939355422.png	new	2025-12-28 16:32:47.773379	\N
222	8348971315	15iaUA4J5rgfAz6isS6BA07idUA9dXl-BW15FMw--7Vg	07.01-14.01 Ala-Med/AA/7days	68	07.01-14.01 IZI 7 days FAIRMONT	Shymkent	Almaty	-	295,2	508,1	-	-	-	-	Double	HB	-	AZHIBEKOV	KURIMBAY	M	-	-	-	-	-	2950	размещение: \nАжибеков Құрымбай\nКосалиева Жанар;\n\nАлибеков Сагит\nКосалиева Гаухар.	-	Nazerke	family	 /app/bull_project/bull_bot/tmp/uploads/bot_upload_1767001683415.png	new	2025-12-29 10:18:42.456386	\N
425	844850166	15iaUA4J5rgfAz6isS6BA07idUA9dXl-BW15FMw--7Vg	16.01-23.01 NQZ/JED	25	16.01-23.01 NIYET econom /7 days	Astana	Astana	NIYET компаниясынан	$350	513.7	-	-	-	-	Quad	HB	-	AUBAKIROVA	NURBIKE	F	28.09.1958	N13417649	14.03.2031	580928450017	N1601/2	$1 350	вместе размещать с TAUKENOVA SHUGA,\nAUBAKIROVA NURBIKE 	+77014134166	AYAZHAN	separate	/app/bull_project/bull_bot/tmp/uploads/bot_upload_1767449466897.pdf	new	2026-01-03 14:14:18.789096	["AUBAKIROVA NURBIKE"]
248	8471984589	15iaUA4J5rgfAz6isS6BA07idUA9dXl-BW15FMw--7Vg	16.01-23.01 NQZ/JED	13	16.01-23.01 NIYET econom /7 days	Astana	Astana	insta lid	350$	511.5	no	-	-	-	Quad	HB	-	SADIKBAYEV	MADALI	F	15.07.1966	-	11.05.2017	660715000262	-	1350$	всех разместить в QDR номера 	-	Zarina 	separate	/app/bull_project/bull_bot/tmp/uploads/bot_upload_1767080619633.png	new	2025-12-30 07:53:52.530443	\N
262	1116499112	1r83RRUKrTQT_9ZeJ9kNMWn6JZFPAfyZkjsrHGSSjoFA	04.02-11.02 Ala-Jed-Med-Ala/7d	9	04.02-11.02 NIYET econom /7d	Almaty	Almaty	Baza	49	512,7	20$	NO	-	NO	Quad	HB	-	INSEBAYEV	SANZHAR	M	-	-	-	-	-	1330	Сандра паспорт скоро отправлю 	87083013563	PERIZAT 	separate	\N	new	2025-12-30 10:21:37.465293	\N
210	1116499112	15iaUA4J5rgfAz6isS6BA07idUA9dXl-BW15FMw--7Vg	14.01-21.01 Ala-Jed/AA/7days	22	14.01-21.01 NIYET econom /7 days	-	Almaty	-	79	495	-	NO	TOUR VISA	NO	Quad	HB	-	KANI	AMIRKHAN	M	07.11.1992	-	-	921107301867	-	1400	Разместить с KANI ADILKHAN\n	+7 705 112 1211	Perizat	family	/app/bull_project/bull_bot/tmp/uploads/bot_upload_1766990145681.png	new	2025-12-29 08:42:18.333956	\N
296	1116499112	15iaUA4J5rgfAz6isS6BA07idUA9dXl-BW15FMw--7Vg	07.01-14.01 Ala-Med/AA/7days	70	07.01-14.01 IZI 7 days FAIRMONT	Almaty	Almaty	Bitrix	24	518,5	-	-	-	-	Double	HB	-	NASSIBOVA	GULESSER	F	10.03.1956	N11034566	26.10.2026	560310400364	-	2950	Русскоязычный гид	87019558848	PERIZAT 	family	/app/bull_project/bull_bot/tmp/uploads/bot_upload_1767177134002.png	new	2025-12-31 11:00:34.436961	["NASSIBOV AZIZ", "NASSIBOVA GULESSER", "AKHMEDOV RUSTAM", "AKHMEDOVA GULCHACHAK"]
459	1116499112	1LXBgCVtqyufEh_qfdxRxImEpMOlHAOTAEKgjHDgCSUA	21.03-28.03/ALA-MED/7d	7	21.03.28.03 HIKMA	Almaty	Almaty	-	400	515,1	-	-	-	-	Double	HB	-	ZHYLTYROVA	ZHANAR	F	18.06.1984	N16085244	11.10.2033	840618450929	-	1850	-	+7 705 575 0607	PERIZAT 	family	/app/bull_project/bull_bot/tmp/uploads/bot_upload_1767528974902.png	new	2026-01-04 12:18:56.709549	["KAUMETOVA BAKTYGUL", "ZHYLTYROVA ZHANAR"]
306	8107860854	15iaUA4J5rgfAz6isS6BA07idUA9dXl-BW15FMw--7Vg	07.01-14.01 Ala-Med/AA/7days	50	07.01-14.01 HIKMA 7 days	Almaty	Almaty	сарафанка	2100$	519.5	100$	-	-	-	Triple	HB	YES	AISA	ISSATAY	M	08.03.2007	N15431287	04.05.2033	070308502175	-	2100$	дать ПОЛНОЦЕННЫЙ TRIPLE НОМЕР, разместить всех вместе  AISA ABYLAY,GABASSOV AZAMAT,AISA ISSATAY	+7 707 251 9033	AIYM	family	/app/bull_project/bull_bot/tmp/uploads/bot_upload_1767179721870.png	new	2025-12-31 11:40:47.450056	["AISA ABYLAY", "AISA ISSATAY", "GABASSOV AZAMAT"]
313	7763611494	1r83RRUKrTQT_9ZeJ9kNMWn6JZFPAfyZkjsrHGSSjoFA	03.02-10.02 Ala-Jed/7d	43	03.02-10.02 NIYET /7d	-	Almaty	лид 	100	519,5	-	-	-	-	Triple	HB	YES	AUYESBEK	ELANURA	F	26.08.1996	N15522516	01.06.2033	960826401669	-	1600	-	-	Bayan	separate	/app/bull_project/bull_bot/tmp/uploads/bot_upload_1767179169399.png	new	2025-12-31 12:02:23.421388	["AUYESBEK ELANURA", "KAPESHOVA AISULU", "ISSABEKOVA ALTYNAY"]
406	8455844577	15iaUA4J5rgfAz6isS6BA07idUA9dXl-BW15FMw--7Vg	17.01-24.01  Ala-Jed/AA/7days	86	17.01-24.01 NIYET /7 days	Almaty	Almaty	Битрикс	50	514.5	25$ от руководства 	-	-	-	Double	HB	YES	DUISENOVA	ALIYA	F	19.09.1979	N18667713	-	790919400144	1701	1625	Скидка 25$ от руководства 	+77789533918	AKTOLKYN	family	/app/bull_project/bull_bot/tmp/uploads/bot_upload_1767358433328.png	new	2026-01-02 12:56:35.983195	["DUISSENOV SABIT", "DUISENOVA ALIYA"]
375	8522155177	15iaUA4J5rgfAz6isS6BA07idUA9dXl-BW15FMw--7Vg	16.01-23.01 NQZ/JED	19	16.01-23.01 NIYET econom /7 days	-	Astana	-	0	516,5	-	Эконом	-	Эконом	Double	HB	-	ZHUMABEKOV	SHYNGYS	M	-	-	-	-	-	1450	сертификат подарили	87026256380	KULYAN	family	\N	new	2026-01-02 07:09:47.734028	["ZHOLDYBEKOV AZAMAT", "ZHUMABEKOV SHYNGYS"]
404	8522155177	15iaUA4J5rgfAz6isS6BA07idUA9dXl-BW15FMw--7Vg	11.01-18.01 Nqz-Med	33	11.01-18.01 NIYET/7days	Abai	Astana	-	0	514,5	-	Эконом	-	Эконом	Double	HB	-	USKEMBAYEV	SULTAN	M	-	-	-	-	-	1650	вместе с USKEMBAYEV RUSLAN	87025567712	KULYAN	separate	\N	new	2026-01-02 12:52:25.641892	["USKEMBAYEV SULTAN"]
190	932021311	15iaUA4J5rgfAz6isS6BA07idUA9dXl-BW15FMw--7Vg	24.01-31.01 Ala-Med/AA/7days	84	24.01-31.01 IZI 7 days	-	Almaty	-	100	495	-	-	-	-	Triple	HB	-	BIARYSTANOVA	GULZHAKHAN	F	09.09.1958	-	22.10.2030	580909400067	-	2150	ЕСТЬ INFANT\n	-	ULZHAN	family	/app/bull_project/bull_bot/tmp/uploads/bot_upload_1766989758079.png	new	2025-12-29 06:30:33.322243	\N
229	932021311	15iaUA4J5rgfAz6isS6BA07idUA9dXl-BW15FMw--7Vg	03.01-10.01 Ala-Jed/AA/7days	12	03.01-10.01NIYET com 7 days	-	Almaty	-	1600	495	-	-	-	-	Quad	HB	-	MASHANLO	NURMUKHAMED	M	05.02.2006	N15714954	15.07.2023	060205500266	-	1600	-	‪+7 708 234 8138‬	ULZHAN	family	/app/bull_project/bull_bot/tmp/uploads/bot_upload_1767015861872.png	new	2025-12-29 13:45:57.865779	\N
231	844850166	15iaUA4J5rgfAz6isS6BA07idUA9dXl-BW15FMw--7Vg	17.01-24.01 Ala-Med/AA/7days	29	17.01-24.01 HIKMA 7 days                                                                      Author’s Tour Nurlan imam	Almaty	Almaty	bitrix	785	514.5	-50$ от руководства	-	-	-	Triple	HB	YES	DUISENBAYEVA	GULSIM	F	-	-	-	-	N1701	$2100	-	-	AYAZHAN	family	\N	new	2025-12-29 13:48:58.937989	\N
171	682201249	15iaUA4J5rgfAz6isS6BA07idUA9dXl-BW15FMw--7Vg	17.01-24.01  Ala-Jed/AA/7days	84	17.01-24.01 NIYET /7 days	-	Almaty	-	1550	495	-	-	-	-	Double	HB	-	RAKHYMBERDIYEV	DAUREN	M	14.10.1993	N14607303	13.07.2032	931014302059	-	1550	 RAKHYMBERDIYEV DAUREN own visa	‪+7 707 934 0966‬	𝓫𝓪𝓴𝓸𝓷𝔂𝓪	family	/app/bull_project/bull_bot/tmp/uploads/bot_upload_1766939379217.png	new	2025-12-28 16:32:48.062804	\N
249	8471984589	15iaUA4J5rgfAz6isS6BA07idUA9dXl-BW15FMw--7Vg	16.01-23.01 NQZ/JED	40	16.01-23.01 NIYET econom /7 days	Astana	Astana	insta lid	350$	509.9	no	-	-	-	Quad	HB	-	KHALMURATOVA	MADINA	F	25.09.1971	N18821789	18.11.2035	710925450595	-	1350$	всех разместить в QDR номера 	-	Zarina 	separate	/app/bull_project/bull_bot/tmp/uploads/bot_upload_1767080659801.png	new	2025-12-30 07:53:53.596683	\N
278	537576032	15iaUA4J5rgfAz6isS6BA07idUA9dXl-BW15FMw--7Vg	07.01-14.01 Ala-Jed/AA/7days	67	07.01-14.01 NIYET 7 days Courtyard	-	Almaty	-	97$	495	-	-	-	-	Triple	HB	-	SAPARGALIYEV	YERASSYL	M	28.05.1997	N16035026	08.10.2033	970528351521	-	2100$	Суперкубок Испаний, и запрос тур на Аль-Ула	+7 708 228 0900	BEKTAY	family	/app/bull_project/bull_bot/tmp/uploads/bot_upload_1767105268120.png	new	2025-12-30 14:39:08.057446	["SAPARGALIYEV YERASSYL", "KAISA AIBAR", "ALI ADIL"]
211	962578877	15iaUA4J5rgfAz6isS6BA07idUA9dXl-BW15FMw--7Vg	07.01-14.01 Ala-Jed/AA/7days	11	07.01-14.01 NIYET econom/7 days	-	Almaty	-	1450	495	-	-	-	-	Double	HB	-	IZATOVA	ZHANNA	F	14.07.1979	N16376965	02.01.2034	790714403342	-	1450	Эконом пакет, виза жоқ скидка басшылықтың рұқсатымен 50$ екі адамға.	+7 775 570 1120	Olzheke	family	/app/bull_project/bull_bot/tmp/uploads/bot_upload_1766998286101.png	new	2025-12-29 09:03:14.037696	\N
263	8455844577	15iaUA4J5rgfAz6isS6BA07idUA9dXl-BW15FMw--7Vg	03.01-10.01 Ala-Jed/AA/7days	22	03.01-10.01NIYET com 7 days	Almaty	Almaty	Битрикс	195	514.5	NO	без авиа	-	без авиа	Double	HB	YES	KALIYEVA	AKKU	F	31.08.1987	N16249512	21.11.2033	870831400956	N0301	1020	БЕЗ АВИА	8 702 101 8777	AKTOLKYN	separate	/app/bull_project/bull_bot/tmp/uploads/bot_upload_1767091087995.png	new	2025-12-30 10:41:44.094717	\N
266	1116499112	1LXBgCVtqyufEh_qfdxRxImEpMOlHAOTAEKgjHDgCSUA	22.03-29.03 NQZ/7d	21	22.03-29.03 Niyet/7 days	Astana	Astana	-	100	512,7	-	NO	-	NO	Double	HB	-	ZHUSIP	TOLENDI	M	-	-	-	-	-	1600	NIYET comfort, train керек \nНомерге қызын указала, данные после нового года	87079263846	PERIZAT 	family	\N	new	2025-12-30 11:07:09.437836	\N
268	1168800932	15iaUA4J5rgfAz6isS6BA07idUA9dXl-BW15FMw--7Vg	18.01-25.01 NQZ-JED/7d	68	18.01-25.01 HIKMA/7d	-	Astana	-	700	495	-	NO	-	NO	Double	HB	-	KAZHIKENOV	ZHASTILEK	M	07.05.1991	N16718900	23.05.2034	910507351467	-	4200	-	77012588292	ADILET	separate	/app/bull_project/bull_bot/tmp/uploads/bot_upload_1767095881230.pdf	new	2025-12-30 11:59:34.009473	["KAZHIKENOV ZHASTILEK", "KAZHIKENOV KABYZHAN"]
269	1168800932	15iaUA4J5rgfAz6isS6BA07idUA9dXl-BW15FMw--7Vg	18.01-25.01 NQZ-JED/7d	69	18.01-25.01 HIKMA/7d	-	Astana	-	700	495	-	NO	-	NO	Double	HB	-	KAZHIKENOV	KABYZHAN	M	-	-	-	-	-	4200	-	77012588292	ADILET	separate	\N	new	2025-12-30 11:59:35.475249	["KAZHIKENOV ZHASTILEK", "KAZHIKENOV KABYZHAN"]
426	844850166	15iaUA4J5rgfAz6isS6BA07idUA9dXl-BW15FMw--7Vg	16.01-23.01 NQZ/JED	26	16.01-23.01 NIYET econom /7 days	Astana	Astana	NIYET компаниясынан	$350	513.7	-	-	-	-	Quad	HB	-	ALIYEVA	ZHADYRA	F	-	-	-	-	N1601/3	$1 350	вместе размещать с TAUKENOVA SHUGA,\nAUBAKIROVA NURBIKE	+7775 690 0840	AYAZHAN	separate	/app/bull_project/bull_bot/tmp/uploads/bot_upload_1767449890187.jpg	new	2026-01-03 14:22:40.006476	["ALIYEVA ZHADYRA"]
428	8455844577	1r83RRUKrTQT_9ZeJ9kNMWn6JZFPAfyZkjsrHGSSjoFA	25.02-04.03 Ala-Jed/7d	5	25.02-04.03 NIYET econom/7d	Almaty	Almaty	Битрикс	390	513.7	-	-	-	-	Quad	HB	-	UALIKHANOV	NURLAN	M	-	-	-	-	-	1550	-	-	AKTOLKYN	separate	\N	new	2026-01-03 16:48:29.405606	["UALIKHANOV NURLAN"]
277	8455844577	15iaUA4J5rgfAz6isS6BA07idUA9dXl-BW15FMw--7Vg	16.01-23.01 NQZ/JED	21	16.01-23.01 NIYET econom /7 days	Astana	Astana	Битрикс	1325	511.5	25$ от руководства 	-	-	-	Quad	HB	-	DOSZHANOV	ARLEN	M	02.08.1986	N13715018	03.08.2031	860802350996	1601N	1325	скидка 25$ от руководства 	+77076260077	AKTOLKYN	separate	/app/bull_project/bull_bot/tmp/uploads/bot_upload_1767096592511.png	new	2025-12-30 12:16:27.525149	["DOSZHANOV ARLEN"]
281	6911557357	15iaUA4J5rgfAz6isS6BA07idUA9dXl-BW15FMw--7Vg	06.01-13.01 Ala-Jed/7d	13	06.01-13.01 NIYET econom/ 7 days	-	Almaty	-	150$	495	-	-	-	-	Triple	HB	-	ORAZKHAN	KHAFIZA	F	17.06.2003	N18405523	02.04.2025	030617601344	-	1350$	бір отбасы	+77714006738	Sagyndyk	family	/app/bull_project/bull_bot/tmp/uploads/bot_upload_1767164754284.png	new	2025-12-31 07:36:42.335624	["ORAZKHAN KHAF", "NURIYEVA ASSIYA", "SIGNATURE BEARER"]
287	8471984589	1r83RRUKrTQT_9ZeJ9kNMWn6JZFPAfyZkjsrHGSSjoFA	08.02-15.02 NQZ-MED/7d	26	08.02-15.02 NIYET/7d	-	Astana	-	100$	495	-	-	-	-	Double	HB	-	UAKHITOV	ZHANAT	M	05.03.1967	N16311540	31.01.2024	670305300016	-	1630$	братья заселить в 1 дабл номере \n20$ дала скидку Кымбат 	-	Zarina 	family	/app/bull_project/bull_bot/tmp/uploads/bot_upload_1767171311425.png	new	2025-12-31 09:00:57.939422	["UAKHITOV ZHANAT", "UAKHITOV ADIL"]
429	682201249	1r83RRUKrTQT_9ZeJ9kNMWn6JZFPAfyZkjsrHGSSjoFA	07.02-14.02.2026 Ala-Med/7d	13	07.02-14.02 HIKMA /7d	-	Almaty	-	350	495	-	-	-	-	Double	HB	-	NARBAYEV	YERBOLAT	M	09.04.1977	N13612620	13.06.2031	770409302207	-	2070	Есть скидка от Назерке	+7 771 562 7222	BAGDAT	family	/app/bull_project/bull_bot/tmp/uploads/bot_upload_1767360666498.png	new	2026-01-04 02:59:43.731256	["NARBAYEV YERBOLAT", "BALTABAYEV DAMIR"]
314	7763611494	1r83RRUKrTQT_9ZeJ9kNMWn6JZFPAfyZkjsrHGSSjoFA	03.02-10.02 Ala-Jed/7d	44	03.02-10.02 NIYET /7d	-	Almaty	лид 	100	519,5	-	-	-	-	Triple	HB	YES	KAPESHOVA	AISULU	F	04.05.1963	N12416123	05.06.2029	630504401626	-	1600	-	-	Bayan	separate	/app/bull_project/bull_bot/tmp/uploads/bot_upload_1767179202867.png	new	2025-12-31 12:02:23.798923	["AUYESBEK ELANURA", "KAPESHOVA AISULU", "ISSABEKOVA ALTYNAY"]
191	932021311	15iaUA4J5rgfAz6isS6BA07idUA9dXl-BW15FMw--7Vg	24.01-31.01 Ala-Med/AA/7days	85	24.01-31.01 IZI 7 days	-	Almaty	-	100	495	-	-	-	-	Triple	HB	-	BEGIZHANOVA	ZERE	F	26.05.1996	-	13.10.2031	960526450021	-	2150	ЕСТЬ INFANT\n	-	ULZHAN	family	/app/bull_project/bull_bot/tmp/uploads/bot_upload_1766989769382.png	new	2025-12-29 06:30:33.98674	\N
458	1116499112	1LXBgCVtqyufEh_qfdxRxImEpMOlHAOTAEKgjHDgCSUA	21.03-28.03/ALA-MED/7d	6	21.03.28.03 HIKMA	Almaty	Almaty	-	400	515,1	-	-	-	-	Double	HB	-	KAUMETOVA	BAKTYGUL	F	01.04.1966	N13923005	23.08.2031	660401401744	-	1850	-	‪+7 701 433 7317‬	PERIZAT 	family	/app/bull_project/bull_bot/tmp/uploads/bot_upload_1767528920959.png	new	2026-01-04 12:18:56.326422	["KAUMETOVA BAKTYGUL", "ZHYLTYROVA ZHANAR"]
250	8471984589	15iaUA4J5rgfAz6isS6BA07idUA9dXl-BW15FMw--7Vg	16.01-23.01 NQZ/JED	41	16.01-23.01 NIYET econom /7 days	Astana	Astana	insta lid	350$	509.9	no	-	-	-	Quad	HB	-	SADIKBAYEVA	NAZIRA	F	16.05.1969	N11769170	21.05.2018	690516000434	-	1350$	всех разместить в QDR номера 	-	Zarina 	separate	/app/bull_project/bull_bot/tmp/uploads/bot_upload_1767080701335.png	new	2025-12-30 07:53:54.569388	\N
427	638331254	1r83RRUKrTQT_9ZeJ9kNMWn6JZFPAfyZkjsrHGSSjoFA	08.02-15.02 NQZ-MED/7d	56	08.02-15.02 HIKMA /7d                                                                          Author’s Tour NURLAN imam	Astana	Almaty	Битрикс	2250	513	-	-	-	-	Double	HB	-	KARIBAYEV	DARKHAN	M	25.07.1988	N16302135	22.01.2034	880725300995	-	2250	-	77012224588	Symbat	separate	/app/bull_project/bull_bot/tmp/uploads/bot_upload_1767450318732.pdf	new	2026-01-03 14:25:57.293132	["KARIBAYEV DARKHAN"]
264	8471984589	15iaUA4J5rgfAz6isS6BA07idUA9dXl-BW15FMw--7Vg	18.01-25.01 NQZ-JED/7d	70	18.01-25.01 HIKMA/7d	Astana	Astana	bitrix	50$	511.5	no	-	-	-	Double	HB	YES	MURAT	ASKAN	M	03.10.1984	N10857068	01.12.2026	841003350961	-	2150$	семья муж с женой	87761853131	Zarina	family	/app/bull_project/bull_bot/tmp/uploads/bot_upload_1767091111164.png	new	2025-12-30 10:41:55.962186	\N
267	1116499112	1LXBgCVtqyufEh_qfdxRxImEpMOlHAOTAEKgjHDgCSUA	22.03-29.03 NQZ/7d	22	22.03-29.03 Niyet/7 days	Astana	Astana	-	100	512,7	-	NO	-	NO	Double	HB	-	MYRZAGALIYEVA	ZAURESH	F	-	-	-	-	-	1600	NIYET comfort, train керек \nНомерге қызын указала, данные после нового года	87079263846	PERIZAT 	family	\N	new	2025-12-30 11:07:10.485129	\N
207	8478709339	15iaUA4J5rgfAz6isS6BA07idUA9dXl-BW15FMw--7Vg	17.01-24.01 Ala-Med/AA/7days	25	17.01-24.01 HIKMA 7 days                                                                      Author’s Tour Nurlan imam	-	Almaty	-	1 960,3	495	-	-	-	-	Triple	HB	-	NUKUSHEVA	MOLDIR	F	27.10.1985	-	23.01.2032	851027401010	-	2150	-	87051475572 	Shyngys	family	/app/bull_project/bull_bot/tmp/uploads/bot_upload_1766995776443.png	new	2025-12-29 08:23:37.143819	\N
212	962578877	15iaUA4J5rgfAz6isS6BA07idUA9dXl-BW15FMw--7Vg	07.01-14.01 Ala-Jed/AA/7days	12	07.01-14.01 NIYET econom/7 days	-	Almaty	-	1450	495	-	-	-	-	Double	HB	-	DAULETKHANOV	AIDOS	M	06.01.2003	N13288659	04.08.2030	030106501954	-	1450	Эконом пакет, виза жоқ скидка басшылықтың рұқсатымен 50$ екі адамға.	-	Olzheke	family	/app/bull_project/bull_bot/tmp/uploads/bot_upload_1766998303327.png	new	2025-12-29 09:03:14.28963	\N
276	6911557357	15iaUA4J5rgfAz6isS6BA07idUA9dXl-BW15FMw--7Vg	28.01-04.02 Ala-Jed/AA/7days	79	28.01-04.02 NIYET /7 days	-	Almaty	-	1500	495	-	-	-	-	Double	HB	-	JAKUBAYEVA	ARDAK	F	31.12.1979	Nl7817453	03.11.2034	791231400028	-	1550	-	87475189679 	Sagyndyk	family	/app/bull_project/bull_bot/tmp/uploads/bot_upload_1767093369029.png	new	2025-12-30 12:08:51.741861	["JAKUBAYEV TUREBI", "JAKUBAYEVA ARDAK"]
282	6911557357	15iaUA4J5rgfAz6isS6BA07idUA9dXl-BW15FMw--7Vg	06.01-13.01 Ala-Jed/7d	14	06.01-13.01 NIYET econom/ 7 days	-	Almaty	-	150$	495	-	-	-	-	Triple	HB	-	NURIYEVA	ASSIYA	F	01.05.1981	-	03.06.2035	-	-	1350$	бір отбасы	+77754342530	Sagyndyk	family	/app/bull_project/bull_bot/tmp/uploads/bot_upload_1767164774611.png	new	2025-12-31 07:36:42.699864	["ORAZKHAN KHAF", "NURIYEVA ASSIYA", "SIGNATURE BEARER"]
315	7763611494	1r83RRUKrTQT_9ZeJ9kNMWn6JZFPAfyZkjsrHGSSjoFA	03.02-10.02 Ala-Jed/7d	45	03.02-10.02 NIYET /7d	-	Almaty	лид 	100	519,5	-	-	-	-	Triple	HB	YES	ISSABEKOVA	ALTYNAY	F	18.07.1974	N14797536	25.09.2032	740718402624	-	1600	-	-	Bayan	separate	/app/bull_project/bull_bot/tmp/uploads/bot_upload_1767179237803.png	new	2025-12-31 12:02:24.158976	["AUYESBEK ELANURA", "KAPESHOVA AISULU", "ISSABEKOVA ALTYNAY"]
297	1116499112	15iaUA4J5rgfAz6isS6BA07idUA9dXl-BW15FMw--7Vg	07.01-14.01 Ala-Med/AA/7days	71	07.01-14.01 IZI 7 days FAIRMONT	Almaty	Almaty	Bitrix	24	518,5	-	-	-	-	Double	HB	-	AKHMEDOV	RUSTAM	M	14.01.1977	N12233023	20.02.2029	770114300049	-	2950	Русскоязычный гид	8708 364 3884	PERIZAT 	family	/app/bull_project/bull_bot/tmp/uploads/bot_upload_1767177158717.png	new	2025-12-31 11:00:34.834726	["NASSIBOV AZIZ", "NASSIBOVA GULESSER", "AKHMEDOV RUSTAM", "AKHMEDOVA GULCHACHAK"]
288	8471984589	1r83RRUKrTQT_9ZeJ9kNMWn6JZFPAfyZkjsrHGSSjoFA	08.02-15.02 NQZ-MED/7d	27	08.02-15.02 NIYET/7d	-	Astana	call centre	100$	516.5	20$	-	-no	-	Double	HB	-yes	UAKHITOV	ADIL	M	19.02.1973	N18936811	18.12.2035	730219350198	-	1630$	братья заселить в 1 дабл номере \n20$ дала скидку Кымбат	-	Zarina	family	/app/bull_project/bull_bot/tmp/uploads/bot_upload_1767171347963.png	new	2025-12-31 09:00:58.396012	["UAKHITOV ZHANAT", "UAKHITOV ADIL"]
431	932021311	15iaUA4J5rgfAz6isS6BA07idUA9dXl-BW15FMw--7Vg	14.01-21.01 Ala-Jed/AA/7days	54	14.01-21.01 NIYET econom /7 days	-	Almaty	-	0	495	-	-	UMRAH VISA	-	Quad	HB	-	SHUGAIV	KAUSAR	F	-	-	-	-	-	0	Сертификат қажы Нұр мүбарак. Визасы дайын	‪+7 747 803 7896‬	ULZHAN	separate	\N	new	2026-01-04 05:21:40.947635	["SHUGAIV KAUSAR"]
432	8442162235	1r83RRUKrTQT_9ZeJ9kNMWn6JZFPAfyZkjsrHGSSjoFA	01.02-08.02 NQZ/7d	61	01.02-08.02 NIYET/7d	-	Astana	-	350	495	-	AirAstana	-	AirAstana	Double	HB	-	TAZHINAZAROVA	NURZHAMAL	F	02.11.1982	N15777752	27.07.2033	821102400956	-	2150	-	77788082226	Nursultan	separate	/app/bull_project/bull_bot/tmp/uploads/bot_upload_1767511163593.pdf	new	2026-01-04 07:20:32.958965	["TAZHINAZAROVA NURZHAMAL"]
324	6253997402	15iaUA4J5rgfAz6isS6BA07idUA9dXl-BW15FMw--7Vg	28.01-04.02 Ala-Med/AA/7days	49	28.01-04.02 IZI FAIRMONT 7 days	-	Almaty	-	345.82	520.5	-	-	-	-	Double	HB	YES	TAURBAYEVA	AIGANYM	F	21.02.1992	N10642569	06.09.2027	920221400018	-	2450	-	-	AKZHOL	family	/app/bull_project/bull_bot/tmp/uploads/bot_upload_1767197157471.png	new	2025-12-31 16:13:58.73478	["KHOJANAZAROV AZAMAT", "SMAILOV ADILZHAN", "KHOJANAZAROV ALISHER", "SANDYBAYEVA MENSULU", "TAURBAYEVA AIGANYM", "KHOJANAZAROV IBRAGIM", "NURLANBEKOVA AINUR", "MUSSINOVA GULZHAN", "SANDYBAYEV MARAT", "MUKANOVA ALTYNAY", "MUKANOV GABIT", "MUSSINOV YERMUKASH"]
325	6253997402	15iaUA4J5rgfAz6isS6BA07idUA9dXl-BW15FMw--7Vg	28.01-04.02 Ala-Med/AA/7days	50	28.01-04.02 IZI FAIRMONT 7 days	-	Almaty	-	345.82	520.5	-	-	-	-	Double	HB	YES	KHOJANAZAROV	IBRAGIM	M	14.06.2012	N14498171	08.06.2032	120614504404	-	2450	-	-	AKZHOL	family	/app/bull_project/bull_bot/tmp/uploads/bot_upload_1767197226042.png	new	2025-12-31 16:13:59.091024	["KHOJANAZAROV AZAMAT", "SMAILOV ADILZHAN", "KHOJANAZAROV ALISHER", "SANDYBAYEVA MENSULU", "TAURBAYEVA AIGANYM", "KHOJANAZAROV IBRAGIM", "NURLANBEKOVA AINUR", "MUSSINOVA GULZHAN", "SANDYBAYEV MARAT", "MUKANOVA ALTYNAY", "MUKANOV GABIT", "MUSSINOV YERMUKASH"]
279	537576032	15iaUA4J5rgfAz6isS6BA07idUA9dXl-BW15FMw--7Vg	07.01-14.01 Ala-Jed/AA/7days	68	07.01-14.01 NIYET 7 days Courtyard	-	Almaty	-	97$	495	-	-	-	-	Triple	HB	-	KAISA	AIBAR	M	02.01.1998	N15968017	21.09.2023	980102350717	-	2100$	Суперкубок Испаний, и запрос тур на Аль-Ула	+7 708 228 0900	BEKTAY	family	/app/bull_project/bull_bot/tmp/uploads/bot_upload_1767105305236.png	new	2025-12-30 14:39:08.865817	["SAPARGALIYEV YERASSYL", "KAISA AIBAR", "ALI ADIL"]
265	8471984589	15iaUA4J5rgfAz6isS6BA07idUA9dXl-BW15FMw--7Vg	18.01-25.01 NQZ-JED/7d	71	18.01-25.01 HIKMA/7d	Astana	Astana	bitrix	50$	511.5	no	-	-	-	Double	HB	YES	AMERKHANOVA	RAIMGUL	F	19.07.1983	N10857067	-	830719451479	-	2150$	семья муж с женой	8 776 181 31 31	Zarina	family	/app/bull_project/bull_bot/tmp/uploads/bot_upload_1767091147274.png	new	2025-12-30 10:41:56.907256	\N
208	8478709339	15iaUA4J5rgfAz6isS6BA07idUA9dXl-BW15FMw--7Vg	17.01-24.01 Ala-Med/AA/7days	26	17.01-24.01 HIKMA 7 days                                                                      Author’s Tour Nurlan imam	-	Almaty	-	1 960,3	495	-	-	-	-	Triple	HB	-	TURSUNBEKOVA	GULBIRA	F	26.05.1971	-	08.04.2031	710526401141	-	2150	-	87051475572 	Shyngys	family	/app/bull_project/bull_bot/tmp/uploads/bot_upload_1766995812993.png	new	2025-12-29 08:23:37.365271	\N
274	8455844577	15iaUA4J5rgfAz6isS6BA07idUA9dXl-BW15FMw--7Vg	16.01-23.01 NQZ/JED	20	16.01-23.01 NIYET econom /7 days	Astana	Astana	Битрикс	1325	511.5	25$ от руководства 	-	-	-	Quad	HB	-	ABISHEV	GIZZAT	M	05.09.1962	N14214165	06.04.2032	620905350322	1601N	1325	скидка 25$ от руководства 	+7 777 536 0410.	AKTOLKYN	separate	/app/bull_project/bull_bot/tmp/uploads/bot_upload_1767096172690.png	new	2025-12-30 12:08:34.195714	["ABISHEV GIZZAT"]
251	8471984589	15iaUA4J5rgfAz6isS6BA07idUA9dXl-BW15FMw--7Vg	16.01-23.01 NQZ/JED	42	16.01-23.01 NIYET econom /7 days	Astana	Astana	insta lid	350$	511.5	no	-	-	-	Quad	HB	-	URAZALIYEV	AZIZBEK	F	21.06.1999	N10987092	11.05.2017	990621000081	-	1350$	всех разместить в QDR номера	-	Zarina	separate	/app/bull_project/bull_bot/tmp/uploads/bot_upload_1767080734083.png	new	2025-12-30 07:53:55.503064	\N
298	1116499112	15iaUA4J5rgfAz6isS6BA07idUA9dXl-BW15FMw--7Vg	07.01-14.01 Ala-Med/AA/7days	72	07.01-14.01 IZI 7 days FAIRMONT	Almaty	Almaty	Bitrix	24	518,5	-	-	-	-	Double	HB	-	AKHMEDOVA	GULCHACHAK	F	05.03.1976	N17954427	17.02.2035	760305400527	-	2950	Русскоязычный гид	87021698888	PERIZAT 	family	/app/bull_project/bull_bot/tmp/uploads/bot_upload_1767177211759.png	new	2025-12-31 11:00:35.210737	["NASSIBOV AZIZ", "NASSIBOVA GULESSER", "AKHMEDOV RUSTAM", "AKHMEDOVA GULCHACHAK"]
283	6911557357	15iaUA4J5rgfAz6isS6BA07idUA9dXl-BW15FMw--7Vg	06.01-13.01 Ala-Jed/7d	15	06.01-13.01 NIYET econom/ 7 days	-	Almaty	-	150$	495	-	-	-	-	Triple	HB	-	NURIYEV	TALGAT	M	02.01.1972	N19036288	18.12.2035	720102300440	-	1350$	бір отбасы	+77714006763	Sagyndyk	family	/app/bull_project/bull_bot/tmp/uploads/bot_upload_1767164834766.png	new	2025-12-31 07:36:43.053926	["ORAZKHAN KHAF", "NURIYEVA ASSIYA", "SIGNATURE BEARER"]
430	682201249	1r83RRUKrTQT_9ZeJ9kNMWn6JZFPAfyZkjsrHGSSjoFA	07.02-14.02.2026 Ala-Med/7d	14	07.02-14.02 HIKMA /7d	-	Almaty	-	350	495	-	-	-	-	Double	HB	-	BALTABAYEV	DAMIR	M	16.11.1989	N10828945	25.09.2026	891116301957	-	2070	Есть скидка от Назерке	‪+7 778 938 8889‬	BAGDAT	family	/app/bull_project/bull_bot/tmp/uploads/bot_upload_1767360806503.png	new	2026-01-04 02:59:44.232015	["NARBAYEV YERBOLAT", "BALTABAYEV DAMIR"]
434	8442162235	15iaUA4J5rgfAz6isS6BA07idUA9dXl-BW15FMw--7Vg	28.01-04.02 Ala-Jed/AA/7days	7	28.01-04.02 NIYET econom /7 days	-	Almaty	-	350	495	-	AirAstana	-	AirAstana	Quad	HB	-	MEIRBEKOVA	DINARA	F	11.05.1970	-	14.09.2030	700511401465	-	1500	Уже с нами летают 5 раз, скидка согласовано с руководителям 	+7 701 556 9394	Nursultan	family	/app/bull_project/bull_bot/tmp/uploads/bot_upload_1767513364746.png	new	2026-01-04 07:59:56.074944	["MEIRBEKOVA GULSAYA", "MEIRBEKOVA DINARA", "MEIRBEKOVA BAYAN", "GABBASSOVA ALIYA"]
305	8107860854	15iaUA4J5rgfAz6isS6BA07idUA9dXl-BW15FMw--7Vg	07.01-14.01 Ala-Med/AA/7days	49	07.01-14.01 HIKMA 7 days	Almaty	Almaty	сарафанка	2100$	519.5	100$	-	-	-	Triple	HB	YES	AISA	ABYLAY	M	01.08.2004	N13288959	04.08.2030	040801501865	-	2100$	дать ПОЛНОЦЕННЫЙ TRIPLE НОМЕР, разместить всех вместе  AISA ABYLAY,GABASSOV AZAMAT,AISA ISSATAY	+7 707 251 9033	AIYM	family	/app/bull_project/bull_bot/tmp/uploads/bot_upload_1767179687935.png	new	2025-12-31 11:40:47.071122	["AISA ABYLAY", "AISA ISSATAY", "GABASSOV AZAMAT"]
135	8348971315	15iaUA4J5rgfAz6isS6BA07idUA9dXl-BW15FMw--7Vg	21.01-28.01 Ala-Med/AA/7days	80	21.01-28.01 IZI FAIRMONT 7 days	Astana	Almaty	своя база	100	513,7	-	business upgrade 	-	business upgrade 	Double	HB	-	TEMIRGALIYEVA	BAYAN	F	24.11.1989	N13578724	12.07.2031	891124450380	-	2450	•Train business class & avia RT upgrade Business RT 	-	Nazerke	family	/app/bull_project/bull_bot/tmp/uploads/bot_upload_1766834701885.png	new	2025-12-27 11:29:12.585028	\N
136	8348971315	15iaUA4J5rgfAz6isS6BA07idUA9dXl-BW15FMw--7Vg	21.01-28.01 Ala-Med/AA/7days	81	21.01-28.01 IZI FAIRMONT 7 days	Astana	Almaty	своя база	100	513,7	-	business upgrade 	-	business upgrade 	Double	HB	-	TOKENOV	SHALKAR	M	19.03.1984	N12071733	06.11.2028	840319351162	-	2450	•Train business class & avia RT upgrade Business RT 	-	Nazerke	family	/app/bull_project/bull_bot/tmp/uploads/bot_upload_1766834729425.png	new	2025-12-27 11:29:12.844773	\N
316	7763611494	15iaUA4J5rgfAz6isS6BA07idUA9dXl-BW15FMw--7Vg	17.01-24.01 Ala-Med/AA/7days	31	17.01-24.01 HIKMA 7 days                                                                      Author’s Tour Nurlan imam	Almaty	Almaty	база	2050	516,5	no	-	-	-	Triple	HB	YES	BURKITBAYEV	FARKHAT	M	04.09.1989	N11590151	15.01.2028	890904301244	-	2050	-	-	Bayan	family	/app/bull_project/bull_bot/tmp/uploads/bot_upload_1767182724193.png	new	2025-12-31 12:09:06.881222	["BURKITBAYEV FARKHAT", "TUGELBAYEVA RAKHIMA", "BURKITBAYEV BAKYT"]
317	7763611494	15iaUA4J5rgfAz6isS6BA07idUA9dXl-BW15FMw--7Vg	17.01-24.01 Ala-Med/AA/7days	32	17.01-24.01 HIKMA 7 days                                                                      Author’s Tour Nurlan imam	Almaty	Almaty	база	2050	516,5	no	-	-	-	Triple	HB	YES	TUGELBAYEVA	RAKHIMA	F	26.08.1963	N18564177	28.07.2035	630826400995	-	2050	-	-	Bayan	family	/app/bull_project/bull_bot/tmp/uploads/bot_upload_1767182767890.png	new	2025-12-31 12:09:07.224701	["BURKITBAYEV FARKHAT", "TUGELBAYEVA RAKHIMA", "BURKITBAYEV BAKYT"]
280	537576032	15iaUA4J5rgfAz6isS6BA07idUA9dXl-BW15FMw--7Vg	07.01-14.01 Ala-Jed/AA/7days	69	07.01-14.01 NIYET 7 days Courtyard	-	Almaty	-	97$	495	-	-	-	-	Triple	HB	-	ALI	ADIL	M	18.03.1997	N14880020	23.11.2032	970318350383	-	2100$	Суперкубок Испаний, и запрос тур на Аль-Ула	+7 707 470 8995	BEKTAY	family	/app/bull_project/bull_bot/tmp/uploads/bot_upload_1767105349264.png	new	2025-12-30 14:39:09.309404	["SAPARGALIYEV YERASSYL", "KAISA AIBAR", "ALI ADIL"]
460	1116499112	1LXBgCVtqyufEh_qfdxRxImEpMOlHAOTAEKgjHDgCSUA	22.03-29.03 NQZ/7d	23	22.03-29.03 Niyet/7 days	Astana	Astana	База	350	513,7	-	-	-	-	Double	HB	-	SHUKERKHAN	AINUR	F	24.09.2000	N17630822	22.01.2035	000924650653	-	1450	-	+7 702 107 6012	PERIZAT 	separate	/app/bull_project/bull_bot/tmp/uploads/bot_upload_1767529283087.pdf	new	2026-01-04 12:22:22.266402	["SHUKERKHAN AINUR"]
323	6253997402	15iaUA4J5rgfAz6isS6BA07idUA9dXl-BW15FMw--7Vg	28.01-04.02 Ala-Med/AA/7days	48	28.01-04.02 IZI FAIRMONT 7 days	-	Almaty	-	345.82	520.5	-	-	-	-	Double	HB	YES	SANDYBAYEVA	MENSULU	F	12.02.1965	N17736770	17.02.2025	650212400251	-	2450	-	-	AKZHOL	family	/app/bull_project/bull_bot/tmp/uploads/bot_upload_1767197135770.png	new	2025-12-31 16:13:58.354494	["KHOJANAZAROV AZAMAT", "SMAILOV ADILZHAN", "KHOJANAZAROV ALISHER", "SANDYBAYEVA MENSULU", "TAURBAYEVA AIGANYM", "KHOJANAZAROV IBRAGIM", "NURLANBEKOVA AINUR", "MUSSINOVA GULZHAN", "SANDYBAYEV MARAT", "MUKANOVA ALTYNAY", "MUKANOV GABIT", "MUSSINOV YERMUKASH"]
331	6253997402	15iaUA4J5rgfAz6isS6BA07idUA9dXl-BW15FMw--7Vg	28.01-04.02 Ala-Med/AA/7days	56	28.01-04.02 IZI FAIRMONT 7 days	-	Almaty	-	345.82	520.5	-	-	-	-	Double	HB	YES	MUSSINOV	YERMUKASH	M	08.08.1966	N11088157	21.06.2027	660808300019	-	2450	-	-	AKZHOL	family	/app/bull_project/bull_bot/tmp/uploads/bot_upload_1767197497682.png	new	2025-12-31 16:14:01.04311	["KHOJANAZAROV AZAMAT", "SMAILOV ADILZHAN", "KHOJANAZAROV ALISHER", "SANDYBAYEVA MENSULU", "TAURBAYEVA AIGANYM", "KHOJANAZAROV IBRAGIM", "NURLANBEKOVA AINUR", "MUSSINOVA GULZHAN", "SANDYBAYEV MARAT", "MUKANOVA ALTYNAY", "MUKANOV GABIT", "MUSSINOV YERMUKASH"]
433	8442162235	15iaUA4J5rgfAz6isS6BA07idUA9dXl-BW15FMw--7Vg	28.01-04.02 Ala-Jed/AA/7days	6	28.01-04.02 NIYET econom /7 days	-	Almaty	-	350	495	-	AirAstana	-	AirAstana	Quad	HB	-	MEIRBEKOVA	GULSAYA	F	12.01.1984	N17017263	11.04.2024	840112401098	-	1500	Уже с нами летают 5 раз, скидка согласовано с руководителям 	+7 701 556 9394	Nursultan	family	/app/bull_project/bull_bot/tmp/uploads/bot_upload_1767513508576.pdf	new	2026-01-04 07:59:55.630277	["MEIRBEKOVA GULSAYA", "MEIRBEKOVA DINARA", "MEIRBEKOVA BAYAN", "GABBASSOVA ALIYA"]
435	8442162235	15iaUA4J5rgfAz6isS6BA07idUA9dXl-BW15FMw--7Vg	28.01-04.02 Ala-Jed/AA/7days	8	28.01-04.02 NIYET econom /7 days	-	Almaty	-	350	495	-	AirAstana	-	AirAstana	Quad	HB	-	MEIRBEKOVA	BAYAN	F	28.07.1975	N17080815	22.04.2034	750728401751	-	1500	Уже с нами летают 5 раз, скидка согласовано с руководителям 	+7 701 556 9394	Nursultan	family	/app/bull_project/bull_bot/tmp/uploads/bot_upload_1767513397579.png	new	2026-01-04 07:59:56.448495	["MEIRBEKOVA GULSAYA", "MEIRBEKOVA DINARA", "MEIRBEKOVA BAYAN", "GABBASSOVA ALIYA"]
461	489877724	15iaUA4J5rgfAz6isS6BA07idUA9dXl-BW15FMw--7Vg	31.01-07.02 Ala-Med/AA/7days	57	31.01-07.02 IZI FAIRMONT 7 days	Almaty	Almaty	Постоянные клиенты 	350	495	-	-	-	-	Double	HB	-	LIROVA	UKHAR	F	05.11.1968	N13291948	17.08.2020	681105499029	-	2450	Муж и жена. Русскоговорящий гид	+77477546928	Айша Аналитик	family	/app/bull_project/bull_bot/tmp/uploads/bot_upload_1767529369025.png	new	2026-01-04 12:28:39.209116	["LIROVA UKHAR", "YULDASHEV LOCHINBEK"]
463	8455844577	15iaUA4J5rgfAz6isS6BA07idUA9dXl-BW15FMw--7Vg	28.01-04.02 Ala-Med/AA/7days	70	28.01-04.02 IZI FAIRMONT 7 days	Almaty	Almaty	Битрикс	100	515.1	-	-	-	-	Double	HB	YES	NIUIRLANULY	NIUIRMUKHAMMED	M	04.03.2005	-	18.03.2021	050304500926	-	2450	NURULLO Таджикистан азаматы	+7 778 910 3558	AKTOLKYN	family	/app/bull_project/bull_bot/tmp/uploads/bot_upload_1767542607021.png	new	2026-01-04 16:06:17.915712	["NIUIRLANULY NIUIRMUKHAMMED", "GAIBULOEV NURULLO"]
464	8455844577	15iaUA4J5rgfAz6isS6BA07idUA9dXl-BW15FMw--7Vg	28.01-04.02 Ala-Med/AA/7days	71	28.01-04.02 IZI FAIRMONT 7 days	Almaty	Almaty	Битрикс	100	515.1	-	-	-	-	Double	HB	YES	GAIBULOEV	NURULLO	M	-	-	-	-	-	2450	NURULLO Таджикистан азаматы	-	AKTOLKYN	family	\N	new	2026-01-04 16:06:18.321029	["NIUIRLANULY NIUIRMUKHAMMED", "GAIBULOEV NURULLO"]
465	844850166	15iaUA4J5rgfAz6isS6BA07idUA9dXl-BW15FMw--7Vg	10.01- 17.01 Ala-Med/7 d	67	10.01- 17.01 IZI Swiss /7 days	Almaty	Almaty	Bitrix	$2 550	515.1	-	-	-	-	Double	HB	YES	TOLYBAY	AINURA	F	18.05.1994	-	-	940518400137	N1001IZI	$2 550	Доплатили $400 за номер, запросили 2 DBL номера. по возможности — QAABA View	+77081111194	AYAZHAN	family	/app/bull_project/bull_bot/tmp/uploads/bot_upload_1767544622277.pdf	new	2026-01-04 16:48:20.464367	["TOLYBAY AINURA", "KAIKIBASSOV DAUREN", "KAIKIBASSOV KOMEKBAY", "ZHORABEKOVA ULZHALGAS"]
466	844850166	15iaUA4J5rgfAz6isS6BA07idUA9dXl-BW15FMw--7Vg	10.01- 17.01 Ala-Med/7 d	68	10.01- 17.01 IZI Swiss /7 days	Almaty	Almaty	Bitrix	$2 550	515.1	-	-	-	-	Double	HB	YES	KAIKIBASSOV	DAUREN	M	10.06.1995	-	-	950610300083	N1001IZI	$2 550	Доплатили $400 за номер, запросили 2 DBL номера. по возможности — QAABA View	+77780010125 	AYAZHAN	family	/app/bull_project/bull_bot/tmp/uploads/bot_upload_1767544635828.pdf	new	2026-01-04 16:48:20.856578	["TOLYBAY AINURA", "KAIKIBASSOV DAUREN", "KAIKIBASSOV KOMEKBAY", "ZHORABEKOVA ULZHALGAS"]
467	844850166	15iaUA4J5rgfAz6isS6BA07idUA9dXl-BW15FMw--7Vg	10.01- 17.01 Ala-Med/7 d	69	10.01- 17.01 IZI Swiss /7 days	Almaty	Almaty	Bitrix	$2 550	515.1	-	-	-	-	Double	HB	YES	KAIKIBASSOV	KOMEKBAY	M	-	-	-	-	N1001IZI	$2 550	Доплатили $400 за номер, запросили 2 DBL номера. по возможности — QAABA View	-	AYAZHAN	family	/app/bull_project/bull_bot/tmp/uploads/bot_upload_1767544720082.pdf	new	2026-01-04 16:48:21.182808	["TOLYBAY AINURA", "KAIKIBASSOV DAUREN", "KAIKIBASSOV KOMEKBAY", "ZHORABEKOVA ULZHALGAS"]
468	844850166	15iaUA4J5rgfAz6isS6BA07idUA9dXl-BW15FMw--7Vg	10.01- 17.01 Ala-Med/7 d	70	10.01- 17.01 IZI Swiss /7 days	Almaty	Almaty	Bitrix	$2 550	515.1	-	-	-	-	Double	HB	YES	ZHORABEKOVA	ULZHALGAS	F	-	-	-	-	N1001IZI	$2 550	Доплатили $400 за номер, запросили 2 DBL номера. по возможности — QAABA View	-	AYAZHAN	family	/app/bull_project/bull_bot/tmp/uploads/bot_upload_1767544313224.png	new	2026-01-04 16:48:21.520746	["TOLYBAY AINURA", "KAIKIBASSOV DAUREN", "KAIKIBASSOV KOMEKBAY", "ZHORABEKOVA ULZHALGAS"]
320	6253997402	15iaUA4J5rgfAz6isS6BA07idUA9dXl-BW15FMw--7Vg	28.01-04.02 Ala-Med/AA/7days	45	28.01-04.02 IZI FAIRMONT 7 days	-	Almaty	-	345.82	520.5	-	-	-	-	Double	HB	YES	KHOJANAZAROV	AZAMAT	M	04.12.1994	N15129593	15.02.2033	941204350083	-	2450	-	-	AKZHOL	family	/app/bull_project/bull_bot/tmp/uploads/bot_upload_1767196985485.png	new	2025-12-31 16:13:57.204741	["KHOJANAZAROV AZAMAT", "SMAILOV ADILZHAN", "KHOJANAZAROV ALISHER", "SANDYBAYEVA MENSULU", "TAURBAYEVA AIGANYM", "KHOJANAZAROV IBRAGIM", "NURLANBEKOVA AINUR", "MUSSINOVA GULZHAN", "SANDYBAYEV MARAT", "MUKANOVA ALTYNAY", "MUKANOV GABIT", "MUSSINOV YERMUKASH"]
436	8442162235	15iaUA4J5rgfAz6isS6BA07idUA9dXl-BW15FMw--7Vg	28.01-04.02 Ala-Jed/AA/7days	9	28.01-04.02 NIYET econom /7 days	-	Almaty	-	350	495	-	AirAstana	-	AirAstana	Quad	HB	-	GABBASSOVA	ALIYA	F	20.07.1968	-	07.09.2033	680720401940	-	1500	Уже с нами летают 5 раз, скидка согласовано с руководителям 	+7 701 556 9394	Nursultan	family	/app/bull_project/bull_bot/tmp/uploads/bot_upload_1767513435644.png	new	2026-01-04 07:59:56.833135	["MEIRBEKOVA GULSAYA", "MEIRBEKOVA DINARA", "MEIRBEKOVA BAYAN", "GABBASSOVA ALIYA"]
437	8442162235	15iaUA4J5rgfAz6isS6BA07idUA9dXl-BW15FMw--7Vg	28.01-04.02 Ala-Jed/AA/7days	80	28.01-04.02 NIYET /7 days	-	Almaty	-	350	495	-	AirAstana	-	AirAstana	Double	HB	-	ISMAILOV	YERLAN	M	28.09.1983	N13042908	24.05.2030	830928301036	-	1600	Уже с нами летают 5 раз, скидка согласовано с руководителям	+7 701 556 9394	Nursultan	family	/app/bull_project/bull_bot/tmp/uploads/bot_upload_1767514027979.pdf	new	2026-01-04 08:08:01.200389	["ISMAILOV YERLAN", "ISMAILOVA AKMARAL"]
462	489877724	15iaUA4J5rgfAz6isS6BA07idUA9dXl-BW15FMw--7Vg	31.01-07.02 Ala-Med/AA/7days	58	31.01-07.02 IZI FAIRMONT 7 days	Almaty	Almaty	Постоянные клиенты 	350	495	-	-	-	-	Double	HB	-	YULDASHEV	LOCHINBEK	M	16.04.1976	N17835356	25.11.2034	760416399098	-	2450	Муж и жена. Русскоговорящий гид	+77784680061	Айша Аналитик	family	/app/bull_project/bull_bot/tmp/uploads/bot_upload_1767529433601.png	new	2026-01-04 12:28:39.687582	["LIROVA UKHAR", "YULDASHEV LOCHINBEK"]
321	6253997402	15iaUA4J5rgfAz6isS6BA07idUA9dXl-BW15FMw--7Vg	28.01-04.02 Ala-Med/AA/7days	46	28.01-04.02 IZI FAIRMONT 7 days	-	Almaty	-	345.82	520.5	-	-	-	-	Double	HB	YES	SMAILOV	ADILZHAN	M	13.01.1989	N12677861	17.09.2019	890113350262	-	2450	-	-	AKZHOL	family	/app/bull_project/bull_bot/tmp/uploads/bot_upload_1767197040577.png	new	2025-12-31 16:13:57.599447	["KHOJANAZAROV AZAMAT", "SMAILOV ADILZHAN", "KHOJANAZAROV ALISHER", "SANDYBAYEVA MENSULU", "TAURBAYEVA AIGANYM", "KHOJANAZAROV IBRAGIM", "NURLANBEKOVA AINUR", "MUSSINOVA GULZHAN", "SANDYBAYEV MARAT", "MUKANOVA ALTYNAY", "MUKANOV GABIT", "MUSSINOV YERMUKASH"]
438	8442162235	15iaUA4J5rgfAz6isS6BA07idUA9dXl-BW15FMw--7Vg	28.01-04.02 Ala-Jed/AA/7days	81	28.01-04.02 NIYET /7 days	-	Almaty	-	350	495	-	AirAstana	-	AirAstana	Double	HB	-	ISMAILOVA	AKMARAL	F	22.09.1979	N17904207	-	790922400130	-	1600	Уже с нами летают 5 раз, скидка согласовано с руководителям	+7 701 556 9394	Nursultan	family	/app/bull_project/bull_bot/tmp/uploads/bot_upload_1767513878505.png	new	2026-01-04 08:08:01.535696	["ISMAILOV YERLAN", "ISMAILOVA AKMARAL"]
439	8442162235	1r83RRUKrTQT_9ZeJ9kNMWn6JZFPAfyZkjsrHGSSjoFA	08.02-15.02 NQZ-MED/7d	49	08.02-15.02 HIKMA /7d                                                                          Author’s Tour NURLAN imam	-	Astana	-	2150	495	-	AirAstana	-	AirAstana	Double	HB	-	KALDAMANOVA	KARAKOZ	F	27.03.1975	N14674940	21.08.2032	750327401385	-	2150	рядом в комнату с женщиной	77755341685	Nursultan	separate	/app/bull_project/bull_bot/tmp/uploads/bot_upload_1767515049247.png	new	2026-01-04 08:26:56.793164	["KALDAMANOVA KARAKOZ"]
440	8471984589	1r83RRUKrTQT_9ZeJ9kNMWn6JZFPAfyZkjsrHGSSjoFA	04.02-11.02 Ala-Jed-Med-Ala/7d	81	04.02-11.02 NIYET /7d	Almaty	Almaty	insta lid	100$	513.7	_	-	-	-	Double	HB	YES	GANIYEV	ISRAFIL	M	11.08.1969	N13286800	-	690811301633	-	1650$	-	-	Zarina 	family	/app/bull_project/bull_bot/tmp/uploads/bot_upload_1767515524849.png	new	2026-01-04 08:37:11.636747	["GANIYEV ISRAFIL", "SIGNATURE BEARER"]
442	932021311	15iaUA4J5rgfAz6isS6BA07idUA9dXl-BW15FMw--7Vg	21.01-28.01 Ala-Med/AA/7days	10	21.01-28.01 NIYET 7 days	-	Almaty	-	200	495	-	-	-	-	Quad	HB	-	SABAZOVA	GULZHAMAL	F	-	-	-	-	-	1500	-	‪+7 708 943 0212‬	ULZHAN	separate	\N	new	2026-01-04 08:50:14.273824	["SABAZOVA GULZHAMAL", "SABAZOV DAUREN", "SABAZOVA 1", "SABAZOVA 2", "SABAZOVA 3"]
447	8471984589	15iaUA4J5rgfAz6isS6BA07idUA9dXl-BW15FMw--7Vg	07.01-14.01 Ala-Med/AA/7days	66	07.01-14.01 IZI 7 days FAIRMONT	-	Almaty	-	100$	495	-	бизнес класс 	-	бизнес класс 	Double	HB	-	MAMUTOV	RUSTAM	M	07.11.1996	N18626780	11.09.2035	961107300063	-	2450$	бизнес класс + вид на Каабу 	-	Zarina 	family	/app/bull_project/bull_bot/tmp/uploads/bot_upload_1767521828877.png	new	2026-01-04 10:20:53.275102	["MAMUTOV RUSTAM", "MAMUTOVA ZAINAB", "MAMUTOV MURAT", "SHAXSIY IMZO"]
452	844850166	15iaUA4J5rgfAz6isS6BA07idUA9dXl-BW15FMw--7Vg	07.01-14.01 Ala-Jed/AA/7days	42	07.01-14.01 NIYET 7 days Courtyard	Shymkent	Almaty	bitrix	$ 150	513.7	-50$ от рукаводство	-	-	-	Double	HB	-	MAKHANBETOVA	GULZAT	F	22.07.1990	N11386546	31.08.2017	900722401761	N0701	$ 1650	-	+7 707 886 1600	AYAZHAN	family	/app/bull_project/bull_bot/tmp/uploads/bot_upload_1767521600018.pdf	new	2026-01-04 10:26:25.028901	["SHALGINBAYEV BEKZAT", "MAKHANBETOVA GULZAT"]
322	6253997402	15iaUA4J5rgfAz6isS6BA07idUA9dXl-BW15FMw--7Vg	28.01-04.02 Ala-Med/AA/7days	47	28.01-04.02 IZI FAIRMONT 7 days	-	Almaty	-	345.82	520.5	-	-	-	-	Double	HB	YES	KHOJANAZAROV	ALISHER	M	12.01.1988	N13947794	06.10.2031	880112300249	-	2450	-	-	AKZHOL	family	/app/bull_project/bull_bot/tmp/uploads/bot_upload_1767197073147.png	new	2025-12-31 16:13:57.978116	["KHOJANAZAROV AZAMAT", "SMAILOV ADILZHAN", "KHOJANAZAROV ALISHER", "SANDYBAYEVA MENSULU", "TAURBAYEVA AIGANYM", "KHOJANAZAROV IBRAGIM", "NURLANBEKOVA AINUR", "MUSSINOVA GULZHAN", "SANDYBAYEV MARAT", "MUKANOVA ALTYNAY", "MUKANOV GABIT", "MUSSINOV YERMUKASH"]
443	932021311	15iaUA4J5rgfAz6isS6BA07idUA9dXl-BW15FMw--7Vg	21.01-28.01 Ala-Med/AA/7days	6	21.01-28.01 NIYET 7 days	-	Almaty	-	200	495	-	-	-	-	Quad	HB	-	SABAZOV	DAUREN	M	16.06.1993	N13472541	21.01.2031	930616301417	-	1500	-	‪+7 708 943 0212‬	ULZHAN	separate	/app/bull_project/bull_bot/tmp/uploads/bot_upload_1767516459073.png	new	2026-01-04 08:50:17.064585	["SABAZOVA GULZHAMAL", "SABAZOV DAUREN", "SABAZOVA 1", "SABAZOVA 2", "SABAZOVA 3"]
441	8471984589	1r83RRUKrTQT_9ZeJ9kNMWn6JZFPAfyZkjsrHGSSjoFA	04.02-11.02 Ala-Jed-Med-Ala/7d	82	04.02-11.02 NIYET /7d	Almaty	Almaty	insta lid	100$	513.7	_	-	-	-	Double	HB	YES	GANIYEVA	ADELYAT	F	21.01.1974	N13286810	26.07.2030	740121402728	-	1650$	-	-	Zarina 	family	/app/bull_project/bull_bot/tmp/uploads/bot_upload_1767515545434.png	new	2026-01-04 08:37:12.122213	["GANIYEV ISRAFIL", "SIGNATURE BEARER"]
448	8471984589	15iaUA4J5rgfAz6isS6BA07idUA9dXl-BW15FMw--7Vg	07.01-14.01 Ala-Med/AA/7days	67	07.01-14.01 IZI 7 days FAIRMONT	-	Almaty	-	100$	495	-	бизнес класс 	-	бизнес класс 	Double	HB	-	MAMUTOVA	ZAINAB	F	20.09.1993	N11836390	07.06.2028	930920000115	-	2450$	бизнес класс + вид на Каабу 	-	Zarina 	family	/app/bull_project/bull_bot/tmp/uploads/bot_upload_1767521887402.png	new	2026-01-04 10:20:53.723273	["MAMUTOV RUSTAM", "MAMUTOVA ZAINAB", "MAMUTOV MURAT", "SHAXSIY IMZO"]
333	6253997402	15iaUA4J5rgfAz6isS6BA07idUA9dXl-BW15FMw--7Vg	28.01-04.02 Ala-Med/AA/7days	58	28.01-04.02 IZI FAIRMONT 7 days	-	Almaty	-	192.12	495	-	-	-	-	Double	HB	-	SMAILOVA	AIDA	F	27.05.1987	N16196975	24.12.2033	870527400616	-	2450	-	-	AKZHOL	family	/app/bull_project/bull_bot/tmp/uploads/bot_upload_1767197979418.png	new	2025-12-31 16:26:28.551229	["SABITOVA AIGERIM", "SMAILOVA AIDA", "DUISENBIYEV AIDOS"]
444	932021311	15iaUA4J5rgfAz6isS6BA07idUA9dXl-BW15FMw--7Vg	21.01-28.01 Ala-Med/AA/7days	11	21.01-28.01 NIYET 7 days	-	Almaty	-	200	495	-	-	-	-	Quad	HB	-	SABAZOVA	1	F	-	-	-	-	-	1500	-	-	ULZHAN	separate	\N	new	2026-01-04 08:50:17.502266	["SABAZOVA GULZHAMAL", "SABAZOV DAUREN", "SABAZOVA 1", "SABAZOVA 2", "SABAZOVA 3"]
449	8471984589	15iaUA4J5rgfAz6isS6BA07idUA9dXl-BW15FMw--7Vg	07.01-14.01 Ala-Med/AA/7days	74	07.01-14.01 IZI 7 days FAIRMONT	-	Almaty	-	100$	495	-	бизнес класс 	-	бизнес класс 	Double	HB	-	MAMUTOV	MURAT	M	28.11.1993	N16586122	17.05.2024	931128300101	-	2450$	бизнес класс + вид на Каабу 	-	Zarina 	family	/app/bull_project/bull_bot/tmp/uploads/bot_upload_1767521925896.png	new	2026-01-04 10:20:54.103877	["MAMUTOV RUSTAM", "MAMUTOVA ZAINAB", "MAMUTOV MURAT", "SHAXSIY IMZO"]
334	6253997402	15iaUA4J5rgfAz6isS6BA07idUA9dXl-BW15FMw--7Vg	28.01-04.02 Ala-Med/AA/7days	59	28.01-04.02 IZI FAIRMONT 7 days	-	Almaty	-	192.12	495	-	-	-	-	Double	HB	-	DUISENBIYEV	AIDOS	M	07.07.1988	N15909642	28.08.2033	880707300570	-	2450	-	-	AKZHOL	family	/app/bull_project/bull_bot/tmp/uploads/bot_upload_1767197996094.png	new	2025-12-31 16:26:28.943302	["SABITOVA AIGERIM", "SMAILOVA AIDA", "DUISENBIYEV AIDOS"]
445	932021311	15iaUA4J5rgfAz6isS6BA07idUA9dXl-BW15FMw--7Vg	21.01-28.01 Ala-Med/AA/7days	12	21.01-28.01 NIYET 7 days	-	Almaty	-	200	495	-	-	-	-	Quad	HB	-	SABAZOVA	2	F	-	-	-	-	-	1500	-	-	ULZHAN	separate	\N	new	2026-01-04 08:50:17.895775	["SABAZOVA GULZHAMAL", "SABAZOV DAUREN", "SABAZOVA 1", "SABAZOVA 2", "SABAZOVA 3"]
337	6253997402	15iaUA4J5rgfAz6isS6BA07idUA9dXl-BW15FMw--7Vg	28.01-04.02 Ala-Med/AA/7days	44	28.01-04.02 IZI FAIRMONT 7 days	-	Almaty	-	105.67	495	-	-	-	-	Double	HB	-	ZHUMAGULOV	RUSTAM	M	28.04.1986	N13368171	-	860428350271	-	2450	-	-	AKZHOL	family	/app/bull_project/bull_bot/tmp/uploads/bot_upload_1767198854358.png	new	2025-12-31 16:36:28.180595	["ZHUMAGULOVA MARZIYA", "IMANMADIYEV ARMAN", "ZHUMAGULOV RUSTAM", "ZHUMAGULOVA TAMARA"]
336	6253997402	15iaUA4J5rgfAz6isS6BA07idUA9dXl-BW15FMw--7Vg	28.01-04.02 Ala-Med/AA/7days	43	28.01-04.02 IZI FAIRMONT 7 days	-	Almaty	-	105.67	495	-	-	-	-	Double	HB	-	IMANMADIYEV	ARMAN	M	31.08.1992	N11724676	26.02.2028	920831350284	-	2450	-	-	AKZHOL	family	/app/bull_project/bull_bot/tmp/uploads/bot_upload_1767198818812.png	new	2025-12-31 16:36:27.859391	["ZHUMAGULOVA MARZIYA", "IMANMADIYEV ARMAN", "ZHUMAGULOV RUSTAM", "ZHUMAGULOVA TAMARA"]
335	6253997402	15iaUA4J5rgfAz6isS6BA07idUA9dXl-BW15FMw--7Vg	28.01-04.02 Ala-Med/AA/7days	42	28.01-04.02 IZI FAIRMONT 7 days	-	Almaty	-	105.67	495	-	-	-	-	Double	HB	-	ZHUMAGULOVA	MARZIYA	F	05.08.1958	N14770276	22.09.2032	580805401189	-	2450	-	-	AKZHOL	family	/app/bull_project/bull_bot/tmp/uploads/bot_upload_1767198769617.png	new	2025-12-31 16:36:27.504417	["ZHUMAGULOVA MARZIYA", "IMANMADIYEV ARMAN", "ZHUMAGULOV RUSTAM", "ZHUMAGULOVA TAMARA"]
451	844850166	15iaUA4J5rgfAz6isS6BA07idUA9dXl-BW15FMw--7Vg	07.01-14.01 Ala-Jed/AA/7days	41	07.01-14.01 NIYET 7 days Courtyard	Shymkent	Almaty	bitrix	$ 150	513.7	-50$ от рукаводство	-	-	-	Double	HB	-	SHALGINBAYEV	BEKZAT	M	22.11.1990	N13760139	17.11.2031	901122301360	N0701	$ 1650	-	+7 702 477 2211	AYAZHAN	family	/app/bull_project/bull_bot/tmp/uploads/bot_upload_1767521590725.pdf	new	2026-01-04 10:26:24.686867	["SHALGINBAYEV BEKZAT", "MAKHANBETOVA GULZAT"]
453	8471984589	15iaUA4J5rgfAz6isS6BA07idUA9dXl-BW15FMw--7Vg	07.01-14.01 Ala-Jed/AA/7days	21	07.01-14.01 NIYET econom/7 days	Almaty	Almaty	-	350	495	-	-	-	-	Double	HB	-	BEKMURZIYEV	BAKHTIYAR	M	05.02.1986	N14291551	26.04.2032	860205300776	-	1350	-	-	Zarina	separate	/app/bull_project/bull_bot/tmp/uploads/bot_upload_1767518972356.png	new	2026-01-04 10:26:53.014348	["BEKMURZIYEV BAKHTIYAR"]
450	8471984589	15iaUA4J5rgfAz6isS6BA07idUA9dXl-BW15FMw--7Vg	07.01-14.01 Ala-Med/AA/7days	75	07.01-14.01 IZI 7 days FAIRMONT	-	Almaty	-	100$	495	-	бизнес класс 	-	бизнес класс 	Double	HB	-	KARI	ROZIYA	M	31.07.2001	FA1021765	-	-	-	2450$	бизнес класс + вид на Каабу 	-	Zarina 	family	/app/bull_project/bull_bot/tmp/uploads/bot_upload_1767521947839.png	new	2026-01-04 10:20:54.484876	["MAMUTOV RUSTAM", "MAMUTOVA ZAINAB", "MAMUTOV MURAT", "SHAXSIY IMZO"]
345	8348971315	15iaUA4J5rgfAz6isS6BA07idUA9dXl-BW15FMw--7Vg	07.01-14.01 Ala-Jed/AA/7days	20	07.01-14.01 NIYET econom/7 days	-	Almaty	-	980	495	-	-	-	-	Quad	HB	-	KHUJAMOV	ABDUGOFFOR	M	-	-	-	-	-	980	5000kazhy	-	Nazerke	separate	/app/bull_project/bull_bot/tmp/uploads/bot_upload_1767264305209.png	new	2026-01-01 10:46:56.698814	["GULOMIDDINOV RUZIMUKHAMMAD", "KHUJAMOV ABDUGOFFOR"]
338	6253997402	15iaUA4J5rgfAz6isS6BA07idUA9dXl-BW15FMw--7Vg	28.01-04.02 Ala-Med/AA/7days	45	28.01-04.02 IZI FAIRMONT 7 days	-	Almaty	-	105.67	520.5	-	-	-	-	Double	HB	-	ZHUMAGULOVA	TAMARA	F	21.04.1991	N13887325	02.11.2031	910421450369	-	2450	-	-	AKZHOL	family	/app/bull_project/bull_bot/tmp/uploads/bot_upload_1767198883560.png	new	2025-12-31 16:36:28.49871	["ZHUMAGULOVA MARZIYA", "IMANMADIYEV ARMAN", "ZHUMAGULOV RUSTAM", "ZHUMAGULOVA TAMARA"]
346	8348971315	15iaUA4J5rgfAz6isS6BA07idUA9dXl-BW15FMw--7Vg	06.01-13.01 Ala-Jed/7d	11	06.01-13.01 NIYET econom/ 7 days	-	Almaty	-	980	495	-	-	-	-	Double	HB	-	TLENOVA	KAMILA	F	15.09.1983	N16327883	23.01.2034	830915400915	-	980	-	87785140140	Nazerke	separate	/app/bull_project/bull_bot/tmp/uploads/bot_upload_1767265746203.png	new	2026-01-01 11:10:15.073173	["TLENOVA KAMILA"]
446	932021311	15iaUA4J5rgfAz6isS6BA07idUA9dXl-BW15FMw--7Vg	21.01-28.01 Ala-Med/AA/7days	13	21.01-28.01 NIYET 7 days	-	Almaty	-	200	495	-	-	-	-	Quad	HB	-	SABAZOVA	3	F	-	-	-	-	-	1500	-	-	ULZHAN	separate	\N	new	2026-01-04 08:50:18.276357	["SABAZOVA GULZHAMAL", "SABAZOV DAUREN", "SABAZOVA 1", "SABAZOVA 2", "SABAZOVA 3"]
342	6253997402	15iaUA4J5rgfAz6isS6BA07idUA9dXl-BW15FMw--7Vg	16.01-23.01 NQZ/JED	22	16.01-23.01 NIYET econom /7 days	-	Astana	-	350	519.5	-	-	-	-	Quad	HB	-	ABDRAKHMANOV	ARDAK	M	30.05.1966	N13565285	-	660530300395	-	1350	-	87017495457	AKZHOL	separate	/app/bull_project/bull_bot/tmp/uploads/bot_upload_1767199988557.png	new	2025-12-31 16:56:18.190109	["ABDRAKHMANOV ARDAK", "ABDRAKHMANOV MAKHME"]
343	6253997402	15iaUA4J5rgfAz6isS6BA07idUA9dXl-BW15FMw--7Vg	16.01-23.01 NQZ/JED	23	16.01-23.01 NIYET econom /7 days	-	Astana	-	350	519.5	-	-	-	-	Quad	HB	-	ABDRAKHMANOV	MAKHMET	M	20.05.1994	N11972449	02.08.2028	940520350138	-	1350	-	-	AKZHOL	separate	/app/bull_project/bull_bot/tmp/uploads/bot_upload_1767200003137.png	new	2025-12-31 16:56:18.508245	["ABDRAKHMANOV ARDAK", "ABDRAKHMANOV MAKHME"]
339	6253997402	15iaUA4J5rgfAz6isS6BA07idUA9dXl-BW15FMw--7Vg	28.01-04.02 Ala-Med/AA/7days	42	28.01-04.02 IZI FAIRMONT 7 days	-	Almaty	-	0	495	-	-	-	-	Double	HB	-	URAZBAYEVA	AKMARAL	F	14.07.1995	N14882744	26.10.2032	950714450844	-	0	за счёт нашей компании, согласовано с Жандос ага	-	AKZHOL	separate	/app/bull_project/bull_bot/tmp/uploads/bot_upload_1767199585954.png	new	2025-12-31 16:48:22.837785	["URAZBAYEVA AKMARAL"]
344	8348971315	15iaUA4J5rgfAz6isS6BA07idUA9dXl-BW15FMw--7Vg	07.01-14.01 Ala-Jed/AA/7days	19	07.01-14.01 NIYET econom/7 days	-	Almaty	-	980	495	-	-	-	-	Quad	HB	-	GULOMIDDINOV	RUZIMUKHAMMAD	M	-	-	-	-	-	980	5000kazhy	+77754147116	Nazerke	separate	/app/bull_project/bull_bot/tmp/uploads/bot_upload_1767264258460.png	new	2026-01-01 10:46:56.233936	["GULOMIDDINOV RUZIMUKHAMMAD", "KHUJAMOV ABDUGOFFOR"]
350	8348971315	15iaUA4J5rgfAz6isS6BA07idUA9dXl-BW15FMw--7Vg	10.01- 17.01 Ala-Med/7 d	10	10.01- 17.01 HIKMA/7 days	-	Almaty	-	0	495	-	-	-	-	Triple	HB	-	RAKHIMZHAN	RAFKAT	M	08.10.1993	N13976418	28.11.2031	931008302224	-	1900	-	+77017877818	Nazerke	family	/app/bull_project/bull_bot/tmp/uploads/bot_upload_1767266071858.png	new	2026-01-01 11:17:46.235644	["RAKHIMZHAN RAFKAT", "SERIKULY TIMUR", "AKZHOLTAYEV MARAT"]
351	8348971315	15iaUA4J5rgfAz6isS6BA07idUA9dXl-BW15FMw--7Vg	10.01- 17.01 Ala-Med/7 d	11	10.01- 17.01 HIKMA/7 days	-	Almaty	-	0	495	-	-	-	-	Triple	HB	-	SERIKULY	TIMUR	M	08.01.1986	N12060688	30.10.2028	860108300719	-	1900	-	-	Nazerke	family	/app/bull_project/bull_bot/tmp/uploads/bot_upload_1767266110625.png	new	2026-01-01 11:17:46.596607	["RAKHIMZHAN RAFKAT", "SERIKULY TIMUR", "AKZHOLTAYEV MARAT"]
352	8348971315	15iaUA4J5rgfAz6isS6BA07idUA9dXl-BW15FMw--7Vg	10.01- 17.01 Ala-Med/7 d	12	10.01- 17.01 HIKMA/7 days	-	Almaty	-	0	495	-	-	-	-	Triple	HB	-	AKZHOLTAYEV	MARAT	M	18.05.1986	N15728781	17.07.2033	860518301766	-	1900	-	-	Nazerke	family	/app/bull_project/bull_bot/tmp/uploads/bot_upload_1767266129636.png	new	2026-01-01 11:17:46.922354	["RAKHIMZHAN RAFKAT", "SERIKULY TIMUR", "AKZHOLTAYEV MARAT"]
355	844850166	15iaUA4J5rgfAz6isS6BA07idUA9dXl-BW15FMw--7Vg	14.01-21.01 Ala-Jed/AA/7days	90	14.01-21.01 NIYET /7 days	Almaty	Almaty	bitrix	100$	516.5	-50$	-	-	-	Double	HB	YES	TALGAT	RUMEISA	F	22.09.2024	N19305051	23.12.2030	240922653577	N1401	$200	INFANT (1 жаста) вместе размещать с YERBOLATOVA AKBOTA, KADYR BEXULTAN	-	AYAZHAN	family	/app/bull_project/bull_bot/tmp/uploads/bot_upload_1767269265373.pdf	new	2026-01-01 12:13:44.489006	["KADYR BEXULTAN", "YERBOLATOVA AKBOTA", "TALGAT RUMEISA"]
354	844850166	15iaUA4J5rgfAz6isS6BA07idUA9dXl-BW15FMw--7Vg	14.01-21.01 Ala-Jed/AA/7days	89	14.01-21.01 NIYET /7 days	Almaty	Almaty	bitrix	350$	516.5	-50$	-	-	-	Double	HB	YES	YERBOLATOVA	AKBOTA	F	22.09.2000	N19039023	22.12.2035	000922650692	N1401	$1 600	2 взр, 1 INFANT (1 жаста)	+7 747 281 0171	AYAZHAN	family	/app/bull_project/bull_bot/tmp/uploads/bot_upload_1767269278988.pdf	new	2026-01-01 12:13:44.09837	["KADYR BEXULTAN", "YERBOLATOVA AKBOTA", "TALGAT RUMEISA"]
353	844850166	15iaUA4J5rgfAz6isS6BA07idUA9dXl-BW15FMw--7Vg	14.01-21.01 Ala-Jed/AA/7days	88	14.01-21.01 NIYET /7 days	Almaty	Almaty	bitrix	350$	516.5	-50$	-	-	-	Double	HB	YES	KADYR	BEXULTAN	M	13.10.1994	N11703187	02.04.2028	941013302065	N1401	$1 600	2 взр, 1 INFANT (1 жаста)	+77073535919	AYAZHAN	family	/app/bull_project/bull_bot/tmp/uploads/bot_upload_1767269298951.pdf	new	2026-01-01 12:13:43.653246	["KADYR BEXULTAN", "YERBOLATOVA AKBOTA", "TALGAT RUMEISA"]
356	537576032	15iaUA4J5rgfAz6isS6BA07idUA9dXl-BW15FMw--7Vg	07.01-14.01 Ala-Jed/AA/7days	32	07.01-14.01 NIYET 7 days Courtyard	-	Almaty	-	1500	495	-	-	-	-	Quad	HB	-	RASHITOV	BEKZAT	M	09.10.2000	N19043731	30.12.2035	001009500748	-	1500	-	‪+7 701 666 8177‬	BEKTAY	separate	/app/bull_project/bull_bot/tmp/uploads/bot_upload_1767270290574.png	new	2026-01-01 12:26:39.597968	["RASHITOV BEKZAT"]
358	417871301	1r83RRUKrTQT_9ZeJ9kNMWn6JZFPAfyZkjsrHGSSjoFA	08.02-15.02 NQZ-MED/7d	51	08.02-15.02 HIKMA /7d                                                                          Author’s Tour NURLAN imam	-	Astana	Bitrix	100	516,5	-	-	-	-	Double	HB	YES	YELEUSSIZOVA	RAIKHANGUL	F	-	-	-	-	-	2250	Alpys с Maida в одной комнате!\nBOLAT с RAIKHANGUL в одной комнате!	+77021122255	Omirkhan	family	/app/bull_project/bull_bot/tmp/uploads/bot_upload_1767270391633.png	new	2026-01-01 12:39:09.835129	["KIZIYEV BOLAT", "YELEUSSIZOVA RAIKHANGUL", "ABENOV ALPYS", "TUSSUPOVA MAIDA"]
377	8455844577	15iaUA4J5rgfAz6isS6BA07idUA9dXl-BW15FMw--7Vg	21.01-28.01 Ala-Jed/AA/7days	78	21.01-28.01 NIYET /7 days	Almaty	Almaty	Битрикс	334	516.5	-	-	TOUR VISA	-	Double	HB	YES	MUKANAYEV	AIDOS	M	10.01.1988	N14970781	11.12.2032	880110302135	2101	1550	визасы бар	+77781007001	AKTOLKYN	separate	/app/bull_project/bull_bot/tmp/uploads/bot_upload_1767338584622.png	new	2026-01-02 07:30:26.207555	["MUKANAYEV AIDOS", "AITZHANOVA MALIKA"]
357	417871301	1r83RRUKrTQT_9ZeJ9kNMWn6JZFPAfyZkjsrHGSSjoFA	08.02-15.02 NQZ-MED/7d	50	08.02-15.02 HIKMA /7d                                                                          Author’s Tour NURLAN imam	-	Astana	Bitrix	100	516,5	-	-	-	-	Double	HB	YES	KIZIYEV	BOLAT	M	-	-	-	-	-	2250	Alpys с Maida в одной комнате!\nBOLAT с RAIKHANGUL в одной комнате!	+77021122255	Omirkhan	family	/app/bull_project/bull_bot/tmp/uploads/bot_upload_1767270963543.png	new	2026-01-01 12:39:09.373263	["KIZIYEV BOLAT", "YELEUSSIZOVA RAIKHANGUL", "ABENOV ALPYS", "TUSSUPOVA MAIDA"]
359	417871301	1r83RRUKrTQT_9ZeJ9kNMWn6JZFPAfyZkjsrHGSSjoFA	08.02-15.02 NQZ-MED/7d	52	08.02-15.02 HIKMA /7d                                                                          Author’s Tour NURLAN imam	-	Astana	Bitrix	100	516,5	-	-	-	-	Double	HB	YES	ABENOV	ALPYS	M	-	-	-	-	-	2250	Alpys с Maida в одной комнате!\nBOLAT с RAIKHANGUL в одной комнате!	+77021122255	Omirkhan	family	/app/bull_project/bull_bot/tmp/uploads/bot_upload_1767270391633.png	new	2026-01-01 12:39:10.214099	["KIZIYEV BOLAT", "YELEUSSIZOVA RAIKHANGUL", "ABENOV ALPYS", "TUSSUPOVA MAIDA"]
360	417871301	1r83RRUKrTQT_9ZeJ9kNMWn6JZFPAfyZkjsrHGSSjoFA	08.02-15.02 NQZ-MED/7d	53	08.02-15.02 HIKMA /7d                                                                          Author’s Tour NURLAN imam	-	Astana	Bitrix	100	516,5	-	-	-	-	Double	HB	YES	TUSSUPOVA	MAIDA	F	-	-	-	-	-	2250	Alpys с Maida в одной комнате!\nBOLAT с RAIKHANGUL в одной комнате!	+77021122255	Omirkhan	family	/app/bull_project/bull_bot/tmp/uploads/bot_upload_1767270391633.png	new	2026-01-01 12:39:10.593857	["KIZIYEV BOLAT", "YELEUSSIZOVA RAIKHANGUL", "ABENOV ALPYS", "TUSSUPOVA MAIDA"]
361	8455844577	15iaUA4J5rgfAz6isS6BA07idUA9dXl-BW15FMw--7Vg	07.01-14.01 Ala-Med/AA/7days	9	07.01-14.01 NIYET 7 days	Almaty	Almaty	Битрикс	350	516.5	-	-	-	-	Quad	HB	YES	KUPEKOVA	SAULE	F	01.01.1966	N11514607	11.01.2018	660101413033	-	1600	-	+7 775 344 2366	AKTOLKYN	separate	/app/bull_project/bull_bot/tmp/uploads/bot_upload_1767276342942.png	new	2026-01-01 14:12:00.52341	["KUPEKOVA SAULE"]
362	682201249	15iaUA4J5rgfAz6isS6BA07idUA9dXl-BW15FMw--7Vg	03.01-10.01 Ala-Jed/AA/7days	54	03.01-10.01 IZI fairmont 7 days	-	Almaty	-	1550	495	-	Business	-	Business	Double	HB	-	ONGGAROV	YERSULTAN	M	16.08.1993	N13232463	29.12.2030	930816302076	-	4300	бизнес по обязательству	-	BAGDAT	separate	/app/bull_project/bull_bot/tmp/uploads/bot_upload_1767284554120.png	new	2026-01-01 16:25:31.031374	["ONGGAROV YERSULTAN"]
367	962578877	15iaUA4J5rgfAz6isS6BA07idUA9dXl-BW15FMw--7Vg	07.01-14.01 Ala-Jed/AA/7days	13	07.01-14.01 NIYET econom/7 days	-	Almaty	-	1450	495	-	-	-	-	Double	HB	-	KARAZHANOV	ABZAL	M	31.12.1981	N12135951	19.12.2028	811231300355	-	1500	Толық төленген виза тексеру керек!	-	Olzhas	family	/app/bull_project/bull_bot/tmp/uploads/bot_upload_1767336522664.png	new	2026-01-02 06:50:23.775324	["KARAZHANOV ABZAL", "KUANYSHOVA ZHANKENTKUL"]
368	962578877	15iaUA4J5rgfAz6isS6BA07idUA9dXl-BW15FMw--7Vg	07.01-14.01 Ala-Jed/AA/7days	14	07.01-14.01 NIYET econom/7 days	-	Almaty	-	1450	495	-	-	-	-	Double	HB	-	KUANYSHOVA	ZHANKENTKUL	F	05.05.1985	N15442741	17.05.2033	850505403121	-	1500	Толық төленген виза тексеру керек!	-	Olzhas	family	/app/bull_project/bull_bot/tmp/uploads/bot_upload_1767336547632.png	new	2026-01-02 06:50:24.25787	["KARAZHANOV ABZAL", "KUANYSHOVA ZHANKENTKUL"]
372	8072854887	15iaUA4J5rgfAz6isS6BA07idUA9dXl-BW15FMw--7Vg	28.01-04.02 Ala-Med/AA/7days	27	28.01-04.02 HIKMA 7 days	-	Almaty	-	1750	495	-	-	-	-	Double	HB	-	VAGAPOV	ABU BAKR	M	28.10.2016	N12359305	01.05.2029	-	-	1000	2 DOUBLE 1 CHILD	+7 776 890 5588	ISLAM	family	/app/bull_project/bull_bot/tmp/uploads/bot_upload_1767336236727.png	new	2026-01-02 06:52:59.611327	["PYKAZVAGAPOV ARBI", "VAGAPOV ABDU", "VAGAPOVA SAFIIYA", "VAGAPOV ABU", "TOKTONBAYEVA AILAZAT"]
371	8072854887	15iaUA4J5rgfAz6isS6BA07idUA9dXl-BW15FMw--7Vg	28.01-04.02 Ala-Med/AA/7days	26	28.01-04.02 HIKMA 7 days	-	Almaty	-	1750	495	-	-	-	-	Double	HB	-	VAGAPOVA	SAFIIYA	F	16.02.2012	N12346515	02.04.2029	120216603002	-	2150	2 DOUBLE 1 CHILD	+7 776 890 5588	ISLAM	family	/app/bull_project/bull_bot/tmp/uploads/bot_upload_1767336223578.png	new	2026-01-02 06:52:59.293662	["PYKAZVAGAPOV ARBI", "VAGAPOV ABDU", "VAGAPOVA SAFIIYA", "VAGAPOV ABU", "TOKTONBAYEVA AILAZAT"]
376	8471984589	1r83RRUKrTQT_9ZeJ9kNMWn6JZFPAfyZkjsrHGSSjoFA	11.02-18.02 Ala-Jed/7d	86	11.02-18.02 NIYET/7d	Almaty	Almaty	bitrix	736	516.5	-	-	-	-	Double	HB	YES	KENESSOV	BOLYSBAY	M	09.03.1999	N15120022	-	990309350161	-	1650$	Женил жинада акшасы бар 380 200тг 	77477990309	Zarina 	separate	/app/bull_project/bull_bot/tmp/uploads/bot_upload_1767338517095.png	new	2026-01-02 07:28:18.497185	["KENESSOV BOLYSBAY"]
373	8072854887	15iaUA4J5rgfAz6isS6BA07idUA9dXl-BW15FMw--7Vg	28.01-04.02 Ala-Med/AA/7days	28	28.01-04.02 HIKMA 7 days	-	Almaty	-	1750	495	-	-	-	-	Double	HB	-	TOKTONBAYEVA	AILAZAT	M	-	N132507359	-	-	-	2150	2 DOUBLE 1 CHILD	+7 776 890 5588	ISLAM	family	/app/bull_project/bull_bot/tmp/uploads/bot_upload_1767336249555.png	new	2026-01-02 06:52:59.952723	["PYKAZVAGAPOV ARBI", "VAGAPOV ABDU", "VAGAPOVA SAFIIYA", "VAGAPOV ABU", "TOKTONBAYEVA AILAZAT"]
370	8072854887	15iaUA4J5rgfAz6isS6BA07idUA9dXl-BW15FMw--7Vg	28.01-04.02 Ala-Med/AA/7days	25	28.01-04.02 HIKMA 7 days	-	Almaty	-	1750	495	-	-	-	-	Double	HB	-	VAGAPOV	ABDU RAKHMAN	M	28.10.2013	N12223390	47.03.2029	131028505481	-	2150	2 DOUBLE 1 CHILD	+7 776 890 5588	ISLAM	family	/app/bull_project/bull_bot/tmp/uploads/bot_upload_1767336205892.png	new	2026-01-02 06:52:58.935033	["PYKAZVAGAPOV ARBI", "VAGAPOV ABDU", "VAGAPOVA SAFIIYA", "VAGAPOV ABU", "TOKTONBAYEVA AILAZAT"]
369	8072854887	15iaUA4J5rgfAz6isS6BA07idUA9dXl-BW15FMw--7Vg	28.01-04.02 Ala-Med/AA/7days	24	28.01-04.02 HIKMA 7 days	-	Almaty	-	1750	495	-	-	-	-	Double	HB	-	VAGAPOV	ARBI	M	08.08.1985	N12115715	23.01.2029	850808301186	-	2150	2 DOUBLE 1 CHILD	+7 776 890 5588	ISLAM	family	/app/bull_project/bull_bot/tmp/uploads/bot_upload_1767336186979.png	new	2026-01-02 06:52:58.56008	["PYKAZVAGAPOV ARBI", "VAGAPOV ABDU", "VAGAPOVA SAFIIYA", "VAGAPOV ABU", "TOKTONBAYEVA AILAZAT"]
378	8455844577	15iaUA4J5rgfAz6isS6BA07idUA9dXl-BW15FMw--7Vg	21.01-28.01 Ala-Jed/AA/7days	79	21.01-28.01 NIYET /7 days	Almaty	Almaty	Битрикс	334	516.5	-	-	TOUR VISA	-	Double	HB	YES	AITZHANOVA	MALIKA	F	06.08.1991	N16250710	21.11.2033	910806400038	2101	1550	визасы бар	+77753083388	AKTOLKYN	separate	/app/bull_project/bull_bot/tmp/uploads/bot_upload_1767338616417.png	new	2026-01-02 07:30:26.564403	["MUKANAYEV AIDOS", "AITZHANOVA MALIKA"]
374	8522155177	15iaUA4J5rgfAz6isS6BA07idUA9dXl-BW15FMw--7Vg	16.01-23.01 NQZ/JED	18	16.01-23.01 NIYET econom /7 days	-	Astana	-	0	516,5	-	Эконом	-	Эконом	Double	HB	-	ZHOLDYBEKOV	AZAMAT	M	09.09.1992	N18644089	-	920909351296	-	1450	сертификат подарили -	87059084626	KULYAN	family	/app/bull_project/bull_bot/tmp/uploads/bot_upload_1767337628749.pdf	new	2026-01-02 07:09:47.349078	["ZHOLDYBEKOV AZAMAT", "ZHUMABEKOV SHYNGYS"]
385	6911557357	15iaUA4J5rgfAz6isS6BA07idUA9dXl-BW15FMw--7Vg	10.01- 17.01 Ala-Jed/7 d	34	10.01- 17.01 IZI Fairmont /7 days	-	Almaty	-	300	495	-	-	-	-	Triple	HB	-	AKHMOLDAYEVA	ALTYNSHASH	F	24.08.1956	N15970808	21.09.2033	560824400824	-	2250	-	+7 775 315 6580	Sagyndyk 	separate	/app/bull_project/bull_bot/tmp/uploads/bot_upload_1767343410917.png	new	2026-01-02 08:55:47.992551	["AKHMOLDAYEVA ALTYNSHASH", "AKMOLDAYEVA BATPA"]
386	6911557357	15iaUA4J5rgfAz6isS6BA07idUA9dXl-BW15FMw--7Vg	10.01- 17.01 Ala-Jed/7 d	35	10.01- 17.01 IZI Fairmont /7 days	-	Almaty	-	300	495	-	-	-	-	Triple	HB	-	AKMOLDAYEVA	BATPA	F	20.04.1958	N18801536	12.12.2025	580420401582	-	2250	-	+7 775 315 6580	Sagyndyk 	separate	/app/bull_project/bull_bot/tmp/uploads/bot_upload_1767343423501.png	new	2026-01-02 08:55:48.323297	["AKHMOLDAYEVA ALTYNSHASH", "AKMOLDAYEVA BATPA"]
387	6911557357	15iaUA4J5rgfAz6isS6BA07idUA9dXl-BW15FMw--7Vg	10.01- 17.01 Ala-Jed/7 d	4	10.01- 17.01 Hikma /7 days	-	Almaty	-	300	495	-	-	-	-	Double	HB	-	ZHANBAYEV	DARKHAN	M	01.02.1994	N10293801	31.03.2026	940201302094	-	2150	-	+7 775 315 6580	Sagyndyk 	family	/app/bull_project/bull_bot/tmp/uploads/bot_upload_1767344234660.png	new	2026-01-02 08:58:20.464268	["ZHANBAYEV DARKHAN", "ZHANBAY ANARBEK"]
388	6911557357	15iaUA4J5rgfAz6isS6BA07idUA9dXl-BW15FMw--7Vg	10.01- 17.01 Ala-Jed/7 d	5	10.01- 17.01 Hikma /7 days	-	Almaty	-	300	495	-	-	-	-	Double	HB	-	ZHANBAY	ANARBEK	M	05.06.1979	N13747170	20.10.2031	790605301773	-	2150	-	+7 775 315 6580	Sagyndyk 	family	/app/bull_project/bull_bot/tmp/uploads/6911557357_p1.png	new	2026-01-02 08:58:20.8419	["ZHANBAYEV DARKHAN", "ZHANBAY ANARBEK"]
392	8442162235	15iaUA4J5rgfAz6isS6BA07idUA9dXl-BW15FMw--7Vg	21.01-28.01 Ala-Med/AA/7days	65	21.01-28.01 IZI FAIRMONT 7 days	-	Almaty	-	2250	495	-	AirAstana	-	AirAstana	Triple	HB	-	ABDUSSATTAROV	ABDULLA	M	-	-	-	-	-	2250	-	+971 56 254 0995	Nursultan	family	/app/bull_project/bull_bot/tmp/uploads/bot_upload_1767350268760.jpeg	new	2026-01-02 10:39:49.778327	["ABDUSSATTAROV ABDULLA", "MIRZAKULOVA AIGUL", "ABDUSATTAROVA ULDIKIZ"]
393	8442162235	15iaUA4J5rgfAz6isS6BA07idUA9dXl-BW15FMw--7Vg	21.01-28.01 Ala-Med/AA/7days	66	21.01-28.01 IZI FAIRMONT 7 days	-	Almaty	-	2250	495	-	AirAstana	-	AirAstana	Triple	HB	-	MIRZAKULOVA	AIGUL	F	-	-	-	-	-	2250	-	+971 56 254 0995	Nursultan	family	/app/bull_project/bull_bot/tmp/uploads/bot_upload_1767350262716.jpeg	new	2026-01-02 10:39:50.153409	["ABDUSSATTAROV ABDULLA", "MIRZAKULOVA AIGUL", "ABDUSATTAROVA ULDIKIZ"]
394	8442162235	15iaUA4J5rgfAz6isS6BA07idUA9dXl-BW15FMw--7Vg	21.01-28.01 Ala-Med/AA/7days	67	21.01-28.01 IZI FAIRMONT 7 days	-	Almaty	-	2250	495	-	AirAstana	-	AirAstana	Triple	HB	-	ABDUSATTAROVA	ULDIKIZ	F	-	-	-	-	-	2250	-	+971 56 254 0995	Nursultan	family	\N	new	2026-01-02 10:39:50.511446	["ABDUSSATTAROV ABDULLA", "MIRZAKULOVA AIGUL", "ABDUSATTAROVA ULDIKIZ"]
395	8522155177	15iaUA4J5rgfAz6isS6BA07idUA9dXl-BW15FMw--7Vg	11.01-18.01 Nqz-Med	32	11.01-18.01 NIYET/7days	Abai	Astana	-	0	514,5	-	Эконом	-	Эконом	Double	HB	-	USKEMBAYEV	RUSLAN	M	10.01.1983	N10532485	-	830110300020	-	1650	сертификат подарили	87478049144	KULYAN	separate	/app/bull_project/bull_bot/tmp/uploads/bot_upload_1767351886467.pdf	new	2026-01-02 11:07:02.747581	["USKEMBAYEV RUSLAN"]
402	8072854887	15iaUA4J5rgfAz6isS6BA07idUA9dXl-BW15FMw--7Vg	03.01-10.01 Ala-Med/AA/7days	81	03.01-10.01 IZI fairmont 7 days	-	Almaty	-	2750	495	-	-	-	-	Double	HB	-	AUTAYEVA	TURSUNAY	F	27.03.1997	N12744043	07.11.2029	970327400104	-	2750	-	+7 747 901 1129	ISLAM	family	/app/bull_project/bull_bot/tmp/uploads/bot_upload_1767357426217.png	new	2026-01-02 12:41:30.36048	["AUTAYEVA TURSUNAY", "AUTAYEV DILMURAT"]
397	932021311	1r83RRUKrTQT_9ZeJ9kNMWn6JZFPAfyZkjsrHGSSjoFA	06.02-13.02 Nqz-MEd/7d	10	06.02-13.02 NIYET econom 7 days	-	Astana	-	100	495	-	-	-	-	Quad	HB	-	MURAT	AIYM	F	-	-	-	-	-	1300	Скидка 50$	+77477090888	ULZHAN	separate	\N	new	2026-01-02 11:08:56.388796	["MURAT AIYM", "IGEMBAYEVA GULAIYM"]
398	932021311	1r83RRUKrTQT_9ZeJ9kNMWn6JZFPAfyZkjsrHGSSjoFA	06.02-13.02 Nqz-MEd/7d	11	06.02-13.02 NIYET econom 7 days	-	Astana	-	100	495	-	-	-	-	Quad	HB	-	IGEMBAYEVA	GULAIYM	F	-	-	-	-	-	1300	Скидка 50$	+77477090888	ULZHAN	separate	\N	new	2026-01-02 11:08:56.716753	["MURAT AIYM", "IGEMBAYEVA GULAIYM"]
403	8072854887	15iaUA4J5rgfAz6isS6BA07idUA9dXl-BW15FMw--7Vg	03.01-10.01 Ala-Med/AA/7days	82	03.01-10.01 IZI fairmont 7 days	-	Almaty	-	2750	495	-	-	-	-	Double	HB	-	AUTAYEV	DILMURAT	M	19.03.1992	N11862191	-	920319300701	-	2750	-	+7 747 901 1129	ISLAM	family	/app/bull_project/bull_bot/tmp/uploads/bot_upload_1767357453128.png	new	2026-01-02 12:41:30.684447	["AUTAYEVA TURSUNAY", "AUTAYEV DILMURAT"]
405	8455844577	15iaUA4J5rgfAz6isS6BA07idUA9dXl-BW15FMw--7Vg	17.01-24.01  Ala-Jed/AA/7days	85	17.01-24.01 NIYET /7 days	Almaty	Almaty	Битрикс	50	514.5	25$ от руководства 	-	-	-	Double	HB	YES	DUISSENOV	SABIT	M	26.01.1975	N17715976	01.09.2034	750126301871	1701	1625	Скидка 25$ от руководства 	+77789533918	AKTOLKYN	family	/app/bull_project/bull_bot/tmp/uploads/bot_upload_1767358406759.png	new	2026-01-02 12:56:35.613595	["DUISSENOV SABIT", "DUISENOVA ALIYA"]
407	932021311	1r83RRUKrTQT_9ZeJ9kNMWn6JZFPAfyZkjsrHGSSjoFA	08.02-15.02 NQZ-MED/7d	13	08.02-15.02 NIYET/7d	-	Astana	-	293	495	-	-	-	-	Quad	HB	-	NASHARBEKOV	SAMAT	M	24.10.1965	N15395871	18.05.2033	651024350242	-	1550	-	+7 701 967 9005	ULZHAN	family	/app/bull_project/bull_bot/tmp/uploads/bot_upload_1767359721153.png	new	2026-01-02 13:17:51.813539	["NASHARBEKOV SAMAT", "NASHARBEKOV ISMAIL"]
408	932021311	1r83RRUKrTQT_9ZeJ9kNMWn6JZFPAfyZkjsrHGSSjoFA	08.02-15.02 NQZ-MED/7d	14	08.02-15.02 NIYET/7d	-	Astana	-	293	495	-	-	-	-	Quad	HB	-	NASHARBEKOV	ISMAIL	M	18.06.1995	N13796332	08.08.2031	950618350428	-	1550	-	+7 701 967 9005	ULZHAN	family	/app/bull_project/bull_bot/tmp/uploads/bot_upload_1767359756856.png	new	2026-01-02 13:17:52.298877	["NASHARBEKOV SAMAT", "NASHARBEKOV ISMAIL"]
72	489877724	15iaUA4J5rgfAz6isS6BA07idUA9dXl-BW15FMw--7Vg	07.01-14.01 Ala-Med/AA/7days	62	07.01-14.01 IZI 7 days FAIRMONT	Almaty	Almaty	-	 4250$ kaspi/ 2.152.625kzt	506,5	-	BUSINESS CLASS	-	BUSINESS CLASS	Single	HB	-	BADAYEV	RUSTAM	M	23.09.1983	N14005012	30.12.2021	830923351005	-	4700$	BUSINESS CLASS, разместить одного, но рядом с номерами BADAYEVA NAZIRA, SHEDID ELINA на одном этаже,просит двуязычного гида	 +77773041025	AIYM	family	/app/bull_project/bull_bot/tmp/uploads/bot_upload_1766824237614.png	new	2025-12-27 08:33:56.279533	\N
289	537576032	15iaUA4J5rgfAz6isS6BA07idUA9dXl-BW15FMw--7Vg	07.01-14.01 Ala-Med/AA/7days	73	07.01-14.01 IZI 7 days FAIRMONT	-	Almaty	-	97$	495	-	-	-	-	Double	HB	-	BEKZHANOV	KUTTYMURAT	M	10.06.1941	N13391290	13.10.2030	410610302068	-	2400$	Запос на BUSINESS CLASS, и запрос на личный трансфер и на личный гид!	+7 777 702 0434	BEKTAY	family	/app/bull_project/bull_bot/tmp/uploads/bot_upload_1767173972930.png	new	2025-12-31 09:46:44.107465	["BEKZHANOV KUTTYMURAT", "TAZHIKBAYEVA AMANKUL", "BEKZHANOV ASKAR", "BEKZHANOVA BAYAN", "MAKHAMBETOV ORAK", "ABDYKALYKOVA BOTAGOZ"]
49	537576032	15iaUA4J5rgfAz6isS6BA07idUA9dXl-BW15FMw--7Vg	07.01-14.01 Ala-Jed/AA/7days	40	07.01-14.01 NIYET 7 days Courtyard	-	Almaty	-	98$	495	-	Эконом	TOUR VISA	Эконом	Quad	HB	-	RAZBEK	ASSYL	M	22.08.1988	N18664102	17.07.2035	880822301693	-	1500$	Сперкубок, матч билеттерін өздері алған!	+7 701 666 8177	BEKTAY	family	/app/bull_project/bull_bot/tmp/uploads/bot_upload_1766753697333.png	new	2025-12-26 13:01:22.437984	\N
48	537576032	15iaUA4J5rgfAz6isS6BA07idUA9dXl-BW15FMw--7Vg	07.01-14.01 Ala-Jed/AA/7days	39	07.01-14.01 NIYET 7 days Courtyard	-	Almaty	-	98$	495	-	Эконом	TOUR VISA	Эконом	Quad	HB	-	NURTAZA	ASLAN	M	13.10.1991	N15798191	30.07.2033	911013302067	-	1500$	Сперкубок, матч билеттерін өздері алған!	+7 701 666 8177	BEKTAY	family	/app/bull_project/bull_bot/tmp/uploads/bot_upload_1766753683912.png	new	2025-12-26 13:01:22.185848	\N
291	537576032	15iaUA4J5rgfAz6isS6BA07idUA9dXl-BW15FMw--7Vg	07.01-14.01 Ala-Med/AA/7days	75	07.01-14.01 IZI 7 days FAIRMONT	-	Almaty	-	97$	495	-	-	-	-	Double	HB	-	BEKZHANOV	ASKAR	M	05.02.1978	N18991914	25.11.2035	780205302903	-	2400$	Запос на BUSINESS CLASS, и запрос на личный трансфер и на личный гид!	+7 777 702 0434	BEKTAY	family	/app/bull_project/bull_bot/tmp/uploads/bot_upload_1767174048492.png	new	2025-12-31 09:46:44.876397	["BEKZHANOV KUTTYMURAT", "TAZHIKBAYEVA AMANKUL", "BEKZHANOV ASKAR", "BEKZHANOVA BAYAN", "MAKHAMBETOV ORAK", "ABDYKALYKOVA BOTAGOZ"]
97	537576032	15iaUA4J5rgfAz6isS6BA07idUA9dXl-BW15FMw--7Vg	23.01-30.01 NQZ/MED/7d	17	23.01-30.01 NIYET econom	-	Astana	-	98$	495	-	-	TOUR VISA	-	Triple	HB	-	KARBAY	SAIRAN	F	26.01.1975	N15694369	12.07.2033	750126400671	-	1300$	-	77054770832	BEKTAY	family	/app/bull_project/bull_bot/tmp/uploads/bot_upload_1766833588050.png	new	2025-12-27 11:08:56.079595	\N
99	537576032	15iaUA4J5rgfAz6isS6BA07idUA9dXl-BW15FMw--7Vg	23.01-30.01 NQZ/MED/7d	19	23.01-30.01 NIYET econom	-	Astana	-	98$	495	-	-	TOUR VISA	-	Triple	HB	-	KIRBITOVA	SAULE	F	15.03.1980	N16168181	03.12.2033	800315400492	-	1300$	-	77054770832	BEKTAY	family	/app/bull_project/bull_bot/tmp/uploads/bot_upload_1766833615682.png	new	2025-12-27 11:08:57.203301	\N
292	537576032	15iaUA4J5rgfAz6isS6BA07idUA9dXl-BW15FMw--7Vg	07.01-14.01 Ala-Med/AA/7days	76	07.01-14.01 IZI 7 days FAIRMONT	-	Almaty	-	97$	495	-	-	-	-	Double	HB	-	BEKZHANOVA	BAYAN	F	14.06.1973	-	17.08.2018	-	-	2400$	Запос на BUSINESS CLASS, и запрос на личный трансфер и на личный гид!	+7 777 702 0434	BEKTAY	family	/app/bull_project/bull_bot/tmp/uploads/bot_upload_1767174107131.png	new	2025-12-31 09:46:45.262223	["BEKZHANOV KUTTYMURAT", "TAZHIKBAYEVA AMANKUL", "BEKZHANOV ASKAR", "BEKZHANOVA BAYAN", "MAKHAMBETOV ORAK", "ABDYKALYKOVA BOTAGOZ"]
216	537576032	15iaUA4J5rgfAz6isS6BA07idUA9dXl-BW15FMw--7Vg	21.01-28.01 Ala-Med/AA/7days	85	21.01-28.01 IZI FAIRMONT 7 days	-	Almaty	-	2300$	495	-	My seat	-	My seat	Double	HB	-	NAZAROVA	ULZHALGAS	F	16.11.1958	N13052442	-	581116401384	-	2300$	Без хадж набора, цена согл с руководстом, запрос на My seat	+7 778 192 4715	BEKTAY	family	/app/bull_project/bull_bot/tmp/uploads/bot_upload_1767001040976.png	new	2025-12-29 09:39:47.033213	\N
47	537576032	15iaUA4J5rgfAz6isS6BA07idUA9dXl-BW15FMw--7Vg	07.01-14.01 Ala-Jed/AA/7days	38	07.01-14.01 NIYET 7 days Courtyard	-	Almaty	-	98$	495	-	Эконом	TOUR VISA	Эконом	Quad	HB	-	SHALAYEV	DAUREN	M	19.06.1988	N12585670	24.06.2019	880619300314	-	1500$	Сперкубок, матч билеттерін өздері алған!	+7 701 666 8177	BEKTAY	family	/app/bull_project/bull_bot/tmp/uploads/bot_upload_1766753673432.png	cancelled	2025-12-26 13:01:21.967252	\N
75	537576032	15iaUA4J5rgfAz6isS6BA07idUA9dXl-BW15FMw--7Vg	10.01- 17.01 Ala-Jed/7 d	50	10.01- 17.01 IZI Fairmont /7 days	-	Almaty	-	194	495	-	-	-	-	Double	HB	-	BEKDAZIMOV	ASKHAT	M	11.06.1993	16338861	08.02.2034	930611300520	-	2450	-	+77012862825	BEKTAY	family	/app/bull_project/bull_bot/tmp/uploads/bot_upload_1766828052730.png	new	2025-12-27 09:38:41.22756	\N
290	537576032	15iaUA4J5rgfAz6isS6BA07idUA9dXl-BW15FMw--7Vg	07.01-14.01 Ala-Med/AA/7days	74	07.01-14.01 IZI 7 days FAIRMONT	-	Almaty	-	97$	495	-	-	-	-	Double	HB	-	TAZHIKBAYEVA	AMANKUL	F	15.08.1950	N10596805	25.02.2026	500815402913	-	2400$	Запос на BUSINESS CLASS, и запрос на личный трансфер и на личный гид!	+7 777 702 0434	BEKTAY	family	/app/bull_project/bull_bot/tmp/uploads/bot_upload_1767174018191.png	new	2025-12-31 09:46:44.49731	["BEKZHANOV KUTTYMURAT", "TAZHIKBAYEVA AMANKUL", "BEKZHANOV ASKAR", "BEKZHANOVA BAYAN", "MAKHAMBETOV ORAK", "ABDYKALYKOVA BOTAGOZ"]
50	537576032	15iaUA4J5rgfAz6isS6BA07idUA9dXl-BW15FMw--7Vg	07.01-14.01 Ala-Jed/AA/7days	59	07.01-14.01 NIYET 7 days Courtyard	-	Almaty	-	98$	495	-	Эконом	TOUR VISA	Эконом	Quad	HB	-	YERMEKBAYEV	BATYRBEK	M	03.04.1991	N15799793	28.07.2033	910403301485	-	1500$	Сперкубок, матч билеттерін өздері алған!	+7 701 666 8177	BEKTAY	family	/app/bull_project/bull_bot/tmp/uploads/bot_upload_1766753710609.png	new	2025-12-26 13:01:22.654126	\N
294	537576032	15iaUA4J5rgfAz6isS6BA07idUA9dXl-BW15FMw--7Vg	07.01-14.01 Ala-Med/AA/7days	78	07.01-14.01 IZI 7 days FAIRMONT	-	Almaty	-	97$	495	-	-	-	-	Double	HB	-	ABDYKALYKOVA	BOTAGOZ	F	22.06.1975	-	17.05.2016	750622402278	-	2400$	Запос на BUSINESS CLASS, и запрос на личный трансфер и на личный гид!	+7 777 702 0434	BEKTAY	family	/app/bull_project/bull_bot/tmp/uploads/bot_upload_1767174164763.png	new	2025-12-31 09:46:46.00436	["BEKZHANOV KUTTYMURAT", "TAZHIKBAYEVA AMANKUL", "BEKZHANOV ASKAR", "BEKZHANOVA BAYAN", "MAKHAMBETOV ORAK", "ABDYKALYKOVA BOTAGOZ"]
293	537576032	15iaUA4J5rgfAz6isS6BA07idUA9dXl-BW15FMw--7Vg	07.01-14.01 Ala-Med/AA/7days	77	07.01-14.01 IZI 7 days FAIRMONT	-	Almaty	-	97$	495	-	-	-	-	Double	HB	-	MAKHAMBETOV	ORAK	M	19.03.1974	-	05.06.2033	740319302525	-	2400$	Запос на BUSINESS CLASS, и запрос на личный трансфер и на личный гид!	+7 777 702 0434	BEKTAY	family	/app/bull_project/bull_bot/tmp/uploads/bot_upload_1767174139697.png	new	2025-12-31 09:46:45.645157	["BEKZHANOV KUTTYMURAT", "TAZHIKBAYEVA AMANKUL", "BEKZHANOV ASKAR", "BEKZHANOVA BAYAN", "MAKHAMBETOV ORAK", "ABDYKALYKOVA BOTAGOZ"]
409	682201249	15iaUA4J5rgfAz6isS6BA07idUA9dXl-BW15FMw--7Vg	10.01- 17.01 Ala-Jed/7 d	30	10.01- 17.01 IZI Fairmont /7 days	-	Almaty	-	0	495	-	-	-	-	Triple	HB	-	BARIKULOVA	BAYAN	F	31.08.1954	N13345486	26.08.2030	540831401123	-	2350	-	-	BAGDAT	separate	/app/bull_project/bull_bot/tmp/uploads/bot_upload_1767359730199.png	new	2026-01-02 13:21:45.864576	["BARIKULOVA BAYAN"]
410	1168800932	15iaUA4J5rgfAz6isS6BA07idUA9dXl-BW15FMw--7Vg	28.01-04.02 Ala-Med/AA/7days	69	28.01-04.02 IZI FAIRMONT 7 days	-	Almaty	-	2950	495	-	NO	-	NO	Double	HB	-	YERSEITOV	ZHADIGER	M	10.01.1962	N620110301	-	620110301729	-	2450	-	+7 (747) 648-04-78	ADILET	separate	/app/bull_project/bull_bot/tmp/uploads/bot_upload_1767423989491.jpeg	new	2026-01-03 07:07:33.034459	["YERSEITOV ZHADIGER"]
411	6911557357	15iaUA4J5rgfAz6isS6BA07idUA9dXl-BW15FMw--7Vg	28.01-04.02 Ala-Med/AA/7days	70	28.01-04.02 IZI FAIRMONT 7 days	-	Almaty	-	65	495	-	-	-	-	Triple	HB	-	ALIMOVA	RAKHIMEM	F	18.01.1968	N12809676	05.12.2029	680118402094	-	2150	-	+77014440092	Sagyndyk	family	/app/bull_project/bull_bot/tmp/uploads/bot_upload_1767425399542.png	new	2026-01-03 08:06:00.965155	["ALIMOVA RAKHIMEM", "ALIMOV ILZATBEK", "AZNABAKIYEVA NILIFAR"]
412	6911557357	15iaUA4J5rgfAz6isS6BA07idUA9dXl-BW15FMw--7Vg	28.01-04.02 Ala-Med/AA/7days	71	28.01-04.02 IZI FAIRMONT 7 days	-	Almaty	-	65	495	-	-	-	-	Triple	HB	-	ALIMOV	ILZATBEK	M	15.09.1963	N16040888	01.10.2033	630915300684	-	2150	-	+77014440092	Sagyndyk	family	/app/bull_project/bull_bot/tmp/uploads/bot_upload_1767425426311.png	new	2026-01-03 08:06:01.414601	["ALIMOVA RAKHIMEM", "ALIMOV ILZATBEK", "AZNABAKIYEVA NILIFAR"]
413	6911557357	15iaUA4J5rgfAz6isS6BA07idUA9dXl-BW15FMw--7Vg	28.01-04.02 Ala-Med/AA/7days	72	28.01-04.02 IZI FAIRMONT 7 days	-	Almaty	-	65	495	-	-	-	-	Triple	HB	-	AZNABAKIYEVA	NILIFAR	M	06.01.1991	N12954108	16.02.2030	-	-	2150	-	+77014440092	Sagyndyk	family	/app/bull_project/bull_bot/tmp/uploads/bot_upload_1767425450979.png	new	2026-01-03 08:06:01.838329	["ALIMOVA RAKHIMEM", "ALIMOV ILZATBEK", "AZNABAKIYEVA NILIFAR"]
414	6911557357	15iaUA4J5rgfAz6isS6BA07idUA9dXl-BW15FMw--7Vg	31.01-07.02 Ala-Med/AA/7days	75	31.01-07.02 IZI FAIRMONT 7 days	-	Almaty	-	65	495	-	-	-	-	Triple	HB	-	AZNABAKIYEVA	NILIFAR	M	06.01.1991	N12954108	16.02.2030	-	-	2150	-	+77014440092	Sagyndyk	separate	\N	new	2026-01-03 08:09:37.537397	["AZNABAKIYEVA NILIFAR"]
454	6911557357	15iaUA4J5rgfAz6isS6BA07idUA9dXl-BW15FMw--7Vg	14.01-21.01 Ala-Jed/AA/7days	24	14.01-21.01 NIYET econom /7 days	-	Almaty	-	1400	495	-	-	-	-	Double	HB	-	RAMAZANOVA	SALTANAT	F	15.02.1976	N14612404	-	760215403047	-	1400	-	87017140129	Sagyndyk	family	/app/bull_project/bull_bot/tmp/uploads/bot_upload_1767526349979.png	new	2026-01-04 11:35:55.247024	["RAMAZANOVA SALTANAT", "MUKANOVA YENGLIK"]
\.


--
-- Data for Name: requests_4u; Type: TABLE DATA; Schema: public; Owner: koyeb-adm
--

COPY public.requests_4u (id, manager_id, manager_name, table_id, dates, pilgrim_count, room_type, status, created_at, created_sheet_name) FROM stdin;
\.


--
-- Data for Name: users; Type: TABLE DATA; Schema: public; Owner: koyeb-adm
--

COPY public.users (telegram_id, full_name, username, role, created_at) FROM stdin;
5059890735	Islam	IslamSiryaev	manager	2025-12-26 07:17:23.097554
1116499112	PERIZAT 	PerizatZhaksybay	manager	2025-12-28 13:22:24.15713
6253997402	AKZHOL	hickmet_astana	manager	2025-12-27 12:07:00.091463
1168800932	ADILET	adiletzs	manager	2025-12-30 11:52:34.159533
638340387	BAYAN	shbony	manager	2025-12-26 08:30:25.214869
8545226868	Aidos	\N	care	2025-12-29 07:31:28.203091
8442162235	Nursultan	\N	manager	2025-12-26 09:55:32.618462
8049744687	Danelya	\N	care	2025-12-30 16:34:08.244319
8308571353	Shyngys	\N	manager	2025-12-29 07:59:28.416388
8478709339	Shyngys	\N	manager	2025-12-29 08:04:33.457438
6825833663	Ерке	\N	care	2025-12-31 07:50:20.555687
8107860854	AIYM	\N	manager	2025-12-26 20:12:38.071146
844850166	AYAZHAN	aiyazhanm	manager	2025-12-29 06:27:44.810559
417871301	Omirkhan	omirkhan	manager	2025-12-26 13:18:36.851494
962578877	Olzhas	KenzhebekOlzhas	manager	2025-12-27 10:18:58.641564
7708752068	Qymbat	\N	manager	2025-12-26 13:56:45.14131
7610459578	Айгерім	aigerimorynbai	admin	2025-12-26 12:06:13.679691
8205083115	Бахыт	\N	admin	2025-12-27 04:57:32.728089
8522155177	KULYAN	\N	manager	2025-12-26 12:32:17.225625
8072854887	ISLAM	\N	manager	2026-01-01 05:39:32.732081
8348971315	best 	\N	admin	2025-12-26 07:19:23.255356
8413412150	best	ph1limelaa	admin	2025-12-26 08:58:00.552591
8539823008	Arsentai	\N	manager	2025-12-31 05:06:08.653801
2025328195	Madi Turkestan	Rismet_Madi	manager	2025-12-26 12:05:20.274249
7763611494	BAYAN	\N	manager	2025-12-26 11:43:18.397633
761594318	bekbergen	lesbekb	manager	2025-12-26 17:27:45.506575
8455844577	AKTOLKYN	\N	manager	2025-12-26 12:13:13.863879
6911557357	Sagyndyk	Sagyndyk_25	manager	2025-12-26 16:04:33.56568
537576032	Bektay 	qaliyevb	manager	2025-12-26 10:25:22.228332
682201249	BAGDAT	\N	manager	2025-12-27 09:34:54.539989
5821196903	Zhandos	ceo_hickmet	admin	2026-01-04 11:22:43.824588
489877724	Айша Аналитик	ph1lomelaa	manager	2025-12-26 07:09:02.65905
8471984589	Zarina 	\N	manager	2025-12-27 06:05:40.073607
638331254	Symbat	\N	manager	2025-12-26 12:56:08.148351
932021311	ULZHAN	Bulanova_Ulzhan	manager	2025-12-27 10:03:32.591581
\.


--
-- Data for Name: рр; Type: TABLE DATA; Schema: public; Owner: koyeb-adm
--

COPY public."рр" (id, created_at, status, guest_first_name, guest_last_name, package_name, price) FROM stdin;
\.


--
-- Name: approval_requests_id_seq; Type: SEQUENCE SET; Schema: public; Owner: koyeb-adm
--

SELECT pg_catalog.setval('public.approval_requests_id_seq', 1, false);


--
-- Name: bookings_id_seq; Type: SEQUENCE SET; Schema: public; Owner: koyeb-adm
--

SELECT pg_catalog.setval('public.bookings_id_seq', 1, false);


--
-- Name: bookings_id_seq1; Type: SEQUENCE SET; Schema: public; Owner: koyeb-adm
--

SELECT pg_catalog.setval('public.bookings_id_seq1', 468, true);


--
-- Name: requests_4u_id_seq; Type: SEQUENCE SET; Schema: public; Owner: koyeb-adm
--

SELECT pg_catalog.setval('public.requests_4u_id_seq', 1, false);


--
-- Name: users_telegram_id_seq; Type: SEQUENCE SET; Schema: public; Owner: koyeb-adm
--

SELECT pg_catalog.setval('public.users_telegram_id_seq', 1, false);


--
-- Name: admin_settings admin_settings_pkey; Type: CONSTRAINT; Schema: public; Owner: koyeb-adm
--

ALTER TABLE ONLY public.admin_settings
    ADD CONSTRAINT admin_settings_pkey PRIMARY KEY (admin_id);


--
-- Name: approval_requests approval_requests_pkey; Type: CONSTRAINT; Schema: public; Owner: koyeb-adm
--

ALTER TABLE ONLY public.approval_requests
    ADD CONSTRAINT approval_requests_pkey PRIMARY KEY (id);


--
-- Name: рр bookings_pkey; Type: CONSTRAINT; Schema: public; Owner: koyeb-adm
--

ALTER TABLE ONLY public."рр"
    ADD CONSTRAINT bookings_pkey PRIMARY KEY (id);


--
-- Name: bookings bookings_pkey1; Type: CONSTRAINT; Schema: public; Owner: koyeb-adm
--

ALTER TABLE ONLY public.bookings
    ADD CONSTRAINT bookings_pkey1 PRIMARY KEY (id);


--
-- Name: requests_4u requests_4u_pkey; Type: CONSTRAINT; Schema: public; Owner: koyeb-adm
--

ALTER TABLE ONLY public.requests_4u
    ADD CONSTRAINT requests_4u_pkey PRIMARY KEY (id);


--
-- Name: users users_pkey; Type: CONSTRAINT; Schema: public; Owner: koyeb-adm
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_pkey PRIMARY KEY (telegram_id);


--
-- Name: bookings bookings_manager_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: koyeb-adm
--

ALTER TABLE ONLY public.bookings
    ADD CONSTRAINT bookings_manager_id_fkey FOREIGN KEY (manager_id) REFERENCES public.users(telegram_id);


--
-- Name: DEFAULT PRIVILEGES FOR SEQUENCES; Type: DEFAULT ACL; Schema: public; Owner: cloud_admin
--

ALTER DEFAULT PRIVILEGES FOR ROLE cloud_admin IN SCHEMA public GRANT ALL ON SEQUENCES TO neon_superuser WITH GRANT OPTION;


--
-- Name: DEFAULT PRIVILEGES FOR TABLES; Type: DEFAULT ACL; Schema: public; Owner: cloud_admin
--

ALTER DEFAULT PRIVILEGES FOR ROLE cloud_admin IN SCHEMA public GRANT ALL ON TABLES TO neon_superuser WITH GRANT OPTION;


--
-- PostgreSQL database dump complete
--

\unrestrict bbeF9GwQSHd7bPLFxnq13JufKnGHmzm9eOEKTjI9vV9H8DXz7aF1p4YfdIy389w

