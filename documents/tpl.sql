# SQL Manager 2007 for MySQL 4.1.2.1
# ---------------------------------------
# Host     : localhost
# Port     : 3306
# Database : tpl


/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8 */;

SET FOREIGN_KEY_CHECKS=0;

#
# Structure for the `tpl_betas_as` table : 
#

CREATE TABLE `tpl_betas_as` (
  `ID` bigint(20) NOT NULL AUTO_INCREMENT,
  PRIMARY KEY (`ID`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8;

#
# Structure for the `tpl_betas_feeback` table : 
#

CREATE TABLE `tpl_betas_feeback` (
  `ID` bigint(20) NOT NULL AUTO_INCREMENT,
  `PROJECT_ID` bigint(20) DEFAULT NULL,
  PRIMARY KEY (`ID`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8;

#
# Structure for the `tpl_betas_release` table : 
#

CREATE TABLE `tpl_betas_release` (
  `ID` bigint(20) NOT NULL AUTO_INCREMENT,
  `PROJECT_ID` bigint(20) DEFAULT NULL,
  `VERSION` varchar(20) DEFAULT NULL,
  `RELEASE_TIME` datetime DEFAULT NULL,
  PRIMARY KEY (`ID`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8;

#
# Structure for the `tpl_creative` table : 
#

CREATE TABLE `tpl_creative` (
  `ID` bigint(20) NOT NULL AUTO_INCREMENT,
  `NAME` varchar(100) DEFAULT NULL,
  `DESCRIPTION` text,
  `CATEGORY_ID` bigint(20) DEFAULT NULL,
  `CREATE_USER_ID` bigint(20) DEFAULT NULL,
  `CREATE_USER_NAME` varchar(80) DEFAULT NULL,
  `CREATE_TIME` datetime DEFAULT NULL,
  `STATUS` int(2) DEFAULT NULL,
  `TAGS` varchar(255) DEFAULT NULL,
  PRIMARY KEY (`ID`)
) ENGINE=MyISAM AUTO_INCREMENT=29 DEFAULT CHARSET=utf8;

#
# Structure for the `tpl_creative_comment` table : 
#

CREATE TABLE `tpl_creative_comment` (
  `ID` bigint(20) NOT NULL AUTO_INCREMENT,
  `CREATIVE_ID` bigint(20) DEFAULT NULL,
  `TITLE` varchar(20) DEFAULT NULL,
  `CONTENT` text,
  `CREATE_USER_ID` bigint(20) DEFAULT NULL,
  `CREATE_USER` varchar(80) DEFAULT NULL,
  `CREATE_TIME` datetime DEFAULT NULL,
  PRIMARY KEY (`ID`)
) ENGINE=MyISAM AUTO_INCREMENT=36 DEFAULT CHARSET=utf8;

#
# Structure for the `tpl_creative_msg_subscribe` table : 
#

CREATE TABLE `tpl_creative_msg_subscribe` (
  `ID` bigint(20) NOT NULL AUTO_INCREMENT,
  `CREATIVE_ID` bigint(20) DEFAULT NULL,
  `MSG_TYPE` int(2) DEFAULT NULL,
  `USER_ID` bigint(20) DEFAULT NULL,
  `USER_NAME` varchar(80) DEFAULT NULL,
  `CREATE_TIME` datetime DEFAULT NULL,
  PRIMARY KEY (`ID`)
) ENGINE=MyISAM AUTO_INCREMENT=10 DEFAULT CHARSET=utf8;

#
# Structure for the `tpl_creative_remark` table : 
#

CREATE TABLE `tpl_creative_remark` (
  `ID` bigint(20) NOT NULL AUTO_INCREMENT,
  `CREATIVE_ID` bigint(20) DEFAULT NULL,
  `TITLE` varchar(100) DEFAULT NULL,
  `CONTENT` text,
  `CREATE_TIME` date DEFAULT NULL,
  `CREATE_USER_ID` bigint(20) DEFAULT NULL,
  `CREATE_USER` varchar(80) DEFAULT NULL,
  `STATUS` int(2) DEFAULT NULL,
  PRIMARY KEY (`ID`)
) ENGINE=MyISAM AUTO_INCREMENT=14 DEFAULT CHARSET=utf8;

#
# Structure for the `tpl_creative_stat` table : 
#

CREATE TABLE `tpl_creative_stat` (
  `ID` bigint(20) NOT NULL AUTO_INCREMENT,
  `CREATIVE_ID` bigint(20) DEFAULT NULL,
  `PUSH` int(11) DEFAULT '0',
  `POLL` int(11) DEFAULT '0',
  `TYPE` int(11) unsigned NOT NULL DEFAULT '0' COMMENT 'DIGG的类型,1 创意2 创意评论',
  PRIMARY KEY (`ID`),
  KEY `Index_2` (`CREATIVE_ID`,`TYPE`) USING BTREE
) ENGINE=MyISAM AUTO_INCREMENT=8 DEFAULT CHARSET=utf8;

#
# Structure for the `tpl_labs_project` table : 
#

CREATE TABLE `tpl_labs_project` (
  `ID` bigint(20) NOT NULL AUTO_INCREMENT,
  `NAME` varchar(50) DEFAULT NULL,
  `DESCRIPTION` varchar(200) DEFAULT NULL,
  `CATEGORY_ID` bigint(20) DEFAULT NULL,
  `CREATIVE_ID` bigint(20) DEFAULT NULL,
  `SVN_URL` varchar(255) DEFAULT NULL,
  `TAGS` varchar(255) DEFAULT NULL,
  `CREATE_USER_ID` bigint(20) DEFAULT NULL,
  `CREATE_USER` varchar(80) DEFAULT NULL,
  `CREATE_TIME` datetime DEFAULT NULL,
  `STATUS` int(2) DEFAULT NULL,
  `ALIWAY_URL` varchar(255) DEFAULT NULL,
  `HUDSON_URL` varchar(255) DEFAULT NULL,
  `SONAR_URL` varchar(255) DEFAULT NULL,
  `JIRA_URL` varchar(255) DEFAULT NULL,
  `DEVELOP_VERSION` varchar(20) DEFAULT '0000-00-00',
  PRIMARY KEY (`ID`)
) ENGINE=MyISAM AUTO_INCREMENT=16 DEFAULT CHARSET=utf8;

#
# Structure for the `tpl_labs_project_comment` table : 
#

CREATE TABLE `tpl_labs_project_comment` (
  `ID` bigint(20) NOT NULL AUTO_INCREMENT,
  `PROJECT_ID` bigint(20) DEFAULT NULL,
  `TITLE` varchar(20) DEFAULT NULL,
  `CONTENT` text,
  `CREATE_USER_ID` bigint(20) DEFAULT NULL,
  `CREATE_USER` varchar(80) DEFAULT NULL,
  `CREATE_TIME` datetime DEFAULT NULL,
  PRIMARY KEY (`ID`)
) ENGINE=MyISAM AUTO_INCREMENT=26 DEFAULT CHARSET=utf8;

#
# Structure for the `tpl_labs_project_doc` table : 
#

CREATE TABLE `tpl_labs_project_doc` (
  `ID` bigint(20) NOT NULL AUTO_INCREMENT,
  `TITLE` varchar(50) DEFAULT NULL,
  `CONTENT` text,
  `TYPE` int(2) DEFAULT NULL,
  `STATUS` int(2) DEFAULT NULL,
  `TAGS` varchar(255) DEFAULT NULL,
  PRIMARY KEY (`ID`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8;

#
# Structure for the `tpl_labs_project_faq` table : 
#

CREATE TABLE `tpl_labs_project_faq` (
  `ID` bigint(20) NOT NULL AUTO_INCREMENT,
  `PROJECT_ID` bigint(20) DEFAULT NULL,
  `QUESTION` text,
  `ANSWER` text,
  `QUESTION_USER_ID` bigint(20) DEFAULT NULL,
  `QUESTION_USER_NAME` varchar(80) DEFAULT NULL,
  `ANSWER_USER_ID` bigint(20) DEFAULT NULL,
  `ANSWER_USER_NAME` varchar(80) DEFAULT NULL,
  `QUESTION_DATETIME` datetime DEFAULT NULL,
  `ANSWER_DATETIME` datetime DEFAULT NULL,
  PRIMARY KEY (`ID`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8;

#
# Structure for the `tpl_labs_project_notice` table : 
#

CREATE TABLE `tpl_labs_project_notice` (
  `ID` bigint(20) NOT NULL AUTO_INCREMENT,
  `PROJECT_ID` bigint(20) DEFAULT NULL,
  `TITLE` varchar(100) DEFAULT NULL,
  `CONTENT` varchar(255) DEFAULT NULL,
  `CREATE_TIME` datetime DEFAULT NULL,
  `USER_ID` bigint(20) DEFAULT NULL,
  `USER_NAME` varchar(80) DEFAULT NULL,
  `STATUS` int(2) DEFAULT NULL,
  PRIMARY KEY (`ID`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8;

#
# Structure for the `tpl_labs_project_task` table : 
#

CREATE TABLE `tpl_labs_project_task` (
  `ID` bigint(20) NOT NULL AUTO_INCREMENT,
  `TITLE` varchar(79) DEFAULT NULL,
  `DESCRIPTION` text,
  `PROJECT_ID` bigint(20) DEFAULT NULL,
  `STATUS` int(2) DEFAULT NULL,
  `FINISH_TIME` datetime DEFAULT NULL,
  `SUBMIT_USER_ID` bigint(20) DEFAULT NULL,
  `SUBMIT_USER_NAME` varchar(80) DEFAULT NULL,
  `DEAL_USER_ID` bigint(20) DEFAULT NULL,
  `DEAL_USER_NAME` varchar(80) DEFAULT NULL,
  `TYPE` int(2) DEFAULT NULL,
  `LEVEL` int(2) DEFAULT NULL,
  `CREATE_TIME` datetime DEFAULT NULL,
  PRIMARY KEY (`ID`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8;

#
# Structure for the `tpl_labs_user_project` table : 
#

CREATE TABLE `tpl_labs_user_project` (
  `ID` bigint(20) NOT NULL AUTO_INCREMENT,
  `USER_ID` bigint(20) DEFAULT NULL,
  `USER_NAME` varchar(80) DEFAULT NULL,
  `PROJECT_ID` bigint(20) DEFAULT NULL,
  `CREATE_TIME` datetime DEFAULT NULL,
  `ROLE` int(11) DEFAULT NULL,
  `JOIN_REASON` varchar(255) DEFAULT NULL,
  `STATUS` int(2) DEFAULT NULL,
  `SVN_ENABLE` int(2) DEFAULT NULL,
  `HUDSON_ENABLE` int(2) DEFAULT NULL,
  PRIMARY KEY (`ID`)
) ENGINE=MyISAM AUTO_INCREMENT=7 DEFAULT CHARSET=utf8;

#
# Structure for the `tpl_project_category` table : 
#

CREATE TABLE `tpl_project_category` (
  `ID` bigint(20) NOT NULL DEFAULT '0',
  `NAME` varchar(40) DEFAULT NULL,
  `DESCRIPTION` varchar(100) DEFAULT NULL,
  `CREATE_TME` datetime DEFAULT NULL,
  `STATUS` int(2) DEFAULT NULL,
  PRIMARY KEY (`ID`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8;

#
# Structure for the `tpl_tag_stat` table : 
#

CREATE TABLE `tpl_tag_stat` (
  `ID` bigint(20) NOT NULL AUTO_INCREMENT,
  `TAG` varchar(255) DEFAULT NULL,
  `CREATIVE_COUNT` int(11) DEFAULT '0',
  `PROJECT_COUNT` int(11) DEFAULT '0',
  PRIMARY KEY (`ID`)
) ENGINE=MyISAM AUTO_INCREMENT=22 DEFAULT CHARSET=utf8;

#
# Structure for the `tpl_user` table : 
#

CREATE TABLE `tpl_user` (
  `ID` bigint(20) NOT NULL AUTO_INCREMENT,
  `NICK` varchar(80) DEFAULT NULL,
  `EMAIL` varchar(255) DEFAULT NULL,
  `PASSWORD` varchar(255) DEFAULT NULL,
  `STATUS` int(2) DEFAULT NULL,
  `CREATE_TIME` datetime DEFAULT NULL,
  PRIMARY KEY (`ID`)
) ENGINE=InnoDB AUTO_INCREMENT=4 DEFAULT CHARSET=utf8;

#
# Structure for the `tpl_user_digg` table : 
#

CREATE TABLE `tpl_user_digg` (
  `ID` int(10) unsigned NOT NULL AUTO_INCREMENT,
  `USER_ID` int(10) unsigned NOT NULL DEFAULT '0',
  `CREATIVE_ID` int(10) unsigned NOT NULL DEFAULT '0',
  `DIGGEST` int(10) unsigned NOT NULL DEFAULT '0',
  `TYPE` int(10) unsigned NOT NULL DEFAULT '0' COMMENT 'DIGG类型，1 创意2创意评论',
  PRIMARY KEY (`ID`),
  KEY `Index_2` (`CREATIVE_ID`,`USER_ID`,`TYPE`) USING BTREE
) ENGINE=MyISAM AUTO_INCREMENT=28 DEFAULT CHARSET=utf8;

#
# Structure for the `tpl_user_msg` table : 
#

CREATE TABLE `tpl_user_msg` (
  `ID` bigint(20) NOT NULL AUTO_INCREMENT,
  `USER_ID` bigint(20) DEFAULT NULL,
  `TITLE` varchar(100) DEFAULT NULL,
  `CONTENT` text,
  `CREATE_TIME` datetime DEFAULT NULL,
  `TYPE` int(2) DEFAULT NULL,
  `OBJ_ID` bigint(20) DEFAULT NULL,
  PRIMARY KEY (`ID`)
) ENGINE=MyISAM AUTO_INCREMENT=9 DEFAULT CHARSET=utf8;

#
# Structure for the `tpl_user_stat` table : 
#

CREATE TABLE `tpl_user_stat` (
  `ID` bigint(20) NOT NULL AUTO_INCREMENT,
  `USER_ID` bigint(20) DEFAULT NULL,
  `USER_NAME` varchar(50) DEFAULT NULL,
  `LAST_LOGIN` datetime DEFAULT NULL,
  `LOGIN_IP` varchar(64) DEFAULT NULL,
  `LOGIN_COUNT` int(11) DEFAULT '0',
  `CREATIVE_COUNT` int(11) DEFAULT '0',
  `CREATIVE_COMMENT_COUNT` int(11) DEFAULT '0',
  `CREATIVE_SUBSCRIBE_COUNT` int(11) DEFAULT '0',
  `PROJECT_COUNT` int(11) DEFAULT '0',
  `JOIN_PROJECT_COUNT` int(11) DEFAULT '0',
  `PROJECT_DOC_COUNT` int(11) DEFAULT '0',
  `PROJECT_TASK_COUNT` int(11) DEFAULT '0',
  `PROJECT_FAQ_Q_COUNT` int(11) DEFAULT '0',
  `PROJECT_FAQ_A_COUNT` int(11) DEFAULT '0',
  `PROJECT_COMMENT_COUNT` int(11) DEFAULT '0',
  PRIMARY KEY (`ID`)
) ENGINE=MyISAM AUTO_INCREMENT=11 DEFAULT CHARSET=utf8;
