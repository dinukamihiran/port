<?php session_start();
//session start to identify login users and etc

/*
 * Message for developers:
 *
 *
 *
 *
 *
 * */



//if(!$_SESSION["computer_number"])
	//die("Please Login");

$connection = mysql_connect("127.0.0.1","root","kasun123");//Connecting to mysql server
//$connection = mysql_connect("slpa.fit11.tk","syscall","syscall123");//Connecting to mysql server

if(!$connection){//test whether the connection has established 
print mysql_error();
die;
}
mysql_select_db("syscall",$connection);//select uni database from mysql engine 





?>
