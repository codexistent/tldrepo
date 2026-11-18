import { useState, type ChangeEvent } from "react";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import { parseRepo } from "../lib/parseRepo";
import { useNavigate } from "react-router";

export default function HomePage() {
  const [value, setValue] = useState<string>("");
  const navigate = useNavigate();

  const handleChange = (e: ChangeEvent<HTMLInputElement>) => {
    setValue(e.target.value);
  };

  const handleClick = () => {
    const result = parseRepo(value);
    if (result != null) {
      console.log(result.owner);
      console.log(result.repo);

      navigate(`/tour/${result.owner}/${result.repo}`);
    } else {
      console.log("Invalid repo link.");
    }
  };

  return (
    <>
      <form onSubmit={(e) => e.preventDefault()}>
        <Input value={value} onChange={handleChange}></Input>
        <Button onClick={handleClick}>Clickity Mee!!</Button>
      </form>
    </>
  );
}
