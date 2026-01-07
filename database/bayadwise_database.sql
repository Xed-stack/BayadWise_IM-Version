-- phpMyAdmin SQL Dump
-- version 5.2.1
-- https://www.phpmyadmin.net/
--
-- Host: 127.0.0.1
-- Generation Time: Jan 06, 2026 at 01:35 PM
-- Server version: 10.4.32-MariaDB
-- PHP Version: 8.0.30

SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
START TRANSACTION;
SET time_zone = "+00:00";


/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;

--
-- Database: `bayadwise_database`
--

-- --------------------------------------------------------

--
-- Table structure for table `bills`
--

CREATE TABLE `bills` (
  `bill_id` int(11) NOT NULL,
  `user_id` int(11) NOT NULL,
  `bill_name` varchar(100) NOT NULL,
  `amount` decimal(10,2) NOT NULL,
  `due_date` date NOT NULL,
  `status` enum('Paid','Unpaid') DEFAULT 'Unpaid',
  `created_at` timestamp NOT NULL DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `bills`
--

INSERT INTO `bills` (`bill_id`, `user_id`, `bill_name`, `amount`, `due_date`, `status`, `created_at`) VALUES
(33, 4, 'Wi-Fi', 1499.00, '2026-01-27', 'Paid', '2026-01-05 17:02:21'),
(34, 4, 'Water', 600.00, '2026-01-25', 'Unpaid', '2026-01-05 17:02:43'),
(35, 5, 'Fleshlight', 350.00, '2026-01-16', 'Paid', '2026-01-05 17:12:22'),
(36, 4, 'Cellphone', 1699.00, '2026-01-22', 'Paid', '2026-01-06 12:19:18');

-- --------------------------------------------------------

--
-- Table structure for table `ipon`
--

CREATE TABLE `ipon` (
  `ipon_id` int(11) NOT NULL,
  `user_id` int(11) NOT NULL,
  `goal_amount` decimal(10,2) NOT NULL,
  `saved_amount` decimal(10,2) DEFAULT 0.00,
  `remaining_amount` decimal(10,2) GENERATED ALWAYS AS (`goal_amount` - `saved_amount`) STORED,
  `days_left` int(11) DEFAULT NULL,
  `created_at` timestamp NOT NULL DEFAULT current_timestamp(),
  `month` int(11) DEFAULT NULL,
  `date_saved` date NOT NULL DEFAULT curdate()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `ipon`
--

INSERT INTO `ipon` (`ipon_id`, `user_id`, `goal_amount`, `saved_amount`, `days_left`, `created_at`, `month`, `date_saved`) VALUES
(17, 4, 21.00, 60.00, NULL, '2026-01-05 17:02:49', 1, '2026-01-06'),
(18, 5, 100.00, 60.00, NULL, '2026-01-05 17:12:32', 1, '2026-01-06');

-- --------------------------------------------------------

--
-- Table structure for table `ipon_details`
--

CREATE TABLE `ipon_details` (
  `ipon_detail_id` int(11) NOT NULL,
  `ipon_id` int(11) NOT NULL,
  `user_id` int(11) NOT NULL,
  `amount` decimal(10,2) NOT NULL,
  `date_added` date NOT NULL,
  `type` enum('daily','extra') DEFAULT 'daily'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Table structure for table `payment_history`
--

CREATE TABLE `payment_history` (
  `payment_id` int(11) NOT NULL,
  `user_id` int(11) NOT NULL,
  `bill_id` int(11) NOT NULL,
  `amount` decimal(10,2) NOT NULL,
  `paid_date` date NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Table structure for table `users`
--

CREATE TABLE `users` (
  `user_id` int(11) NOT NULL,
  `full_name` varchar(100) NOT NULL,
  `username` varchar(50) NOT NULL,
  `password` varchar(255) NOT NULL,
  `role` enum('user','admin') DEFAULT 'user',
  `created_at` timestamp NOT NULL DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `users`
--

INSERT INTO `users` (`user_id`, `full_name`, `username`, `password`, `role`, `created_at`) VALUES
(1, 'Admin', 'admin', 'admin', 'admin', '2026-01-05 16:53:37'),
(4, 'Rica Mae Gregorio', 'kameng', 'chanpangit', 'user', '2026-01-05 17:01:11'),
(5, 'Cristian Paul', 'chan', 'kalbuto', 'user', '2026-01-05 17:11:37'),
(6, 'Peony the Cat', 'peony', 'posa', 'user', '2026-01-05 17:26:04');

--
-- Indexes for dumped tables
--

--
-- Indexes for table `bills`
--
ALTER TABLE `bills`
  ADD PRIMARY KEY (`bill_id`),
  ADD KEY `user_id` (`user_id`);

--
-- Indexes for table `ipon`
--
ALTER TABLE `ipon`
  ADD PRIMARY KEY (`ipon_id`),
  ADD KEY `user_id` (`user_id`);

--
-- Indexes for table `ipon_details`
--
ALTER TABLE `ipon_details`
  ADD PRIMARY KEY (`ipon_detail_id`),
  ADD KEY `ipon_id` (`ipon_id`),
  ADD KEY `user_id` (`user_id`);

--
-- Indexes for table `payment_history`
--
ALTER TABLE `payment_history`
  ADD PRIMARY KEY (`payment_id`),
  ADD KEY `user_id` (`user_id`),
  ADD KEY `bill_id` (`bill_id`);

--
-- Indexes for table `users`
--
ALTER TABLE `users`
  ADD PRIMARY KEY (`user_id`),
  ADD UNIQUE KEY `username` (`username`);

--
-- AUTO_INCREMENT for dumped tables
--

--
-- AUTO_INCREMENT for table `bills`
--
ALTER TABLE `bills`
  MODIFY `bill_id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=37;

--
-- AUTO_INCREMENT for table `ipon`
--
ALTER TABLE `ipon`
  MODIFY `ipon_id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=19;

--
-- AUTO_INCREMENT for table `ipon_details`
--
ALTER TABLE `ipon_details`
  MODIFY `ipon_detail_id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `payment_history`
--
ALTER TABLE `payment_history`
  MODIFY `payment_id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `users`
--
ALTER TABLE `users`
  MODIFY `user_id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=7;

--
-- Constraints for dumped tables
--

--
-- Constraints for table `bills`
--
ALTER TABLE `bills`
  ADD CONSTRAINT `bills_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `users` (`user_id`);

--
-- Constraints for table `ipon`
--
ALTER TABLE `ipon`
  ADD CONSTRAINT `ipon_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `users` (`user_id`);

--
-- Constraints for table `ipon_details`
--
ALTER TABLE `ipon_details`
  ADD CONSTRAINT `ipon_details_ibfk_1` FOREIGN KEY (`ipon_id`) REFERENCES `ipon` (`ipon_id`),
  ADD CONSTRAINT `ipon_details_ibfk_2` FOREIGN KEY (`user_id`) REFERENCES `users` (`user_id`);

--
-- Constraints for table `payment_history`
--
ALTER TABLE `payment_history`
  ADD CONSTRAINT `payment_history_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `users` (`user_id`),
  ADD CONSTRAINT `payment_history_ibfk_2` FOREIGN KEY (`bill_id`) REFERENCES `bills` (`bill_id`);
COMMIT;

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
